"""Train a 784-256-N MLP with NumPy only, from random weights, on MNIST plus any images in data/custom/<label>/.
Writes the model file named in config.toml, with its training results for the Model tab."""
import gzip
import json
import time
import tomllib
import urllib.request
from pathlib import Path

import numpy as np

URL = "https://storage.googleapis.com/cvdf-datasets/mnist/"
DATA = Path(__file__).parent / "data"
CUSTOM = DATA / "custom"  # one folder per label, named after it, holding images of it: data/custom/A/001.png
DIGITS = [str(d) for d in range(10)]


def load_mnist(split):
    """Images as (n, 784) float32 in 0..1, labels as (n,) int."""
    prefix = "train" if split == "train" else "t10k"
    out = []
    for name, offset in ((f"{prefix}-images-idx3-ubyte.gz", 16), (f"{prefix}-labels-idx1-ubyte.gz", 8)):
        path = DATA / name
        if not path.exists():
            DATA.mkdir(exist_ok=True)
            urllib.request.urlretrieve(URL + name, path)
        out.append(np.frombuffer(gzip.decompress(path.read_bytes()), np.uint8, offset=offset))
    images, labels = out
    return images.reshape(-1, 784).astype(np.float32) / 255, labels.astype(int)


def center_of_mass(img):
    """Shift a 28x28 image so its center of mass sits in the middle, as MNIST does."""
    total = img.sum()
    if total == 0:
        return img
    ys, xs = np.indices(img.shape)
    dy, dx = round(13.5 - (ys * img).sum() / total), round(13.5 - (xs * img).sum() / total)
    return np.roll(img, (dy, dx), axis=(0, 1))


def load_image(path):
    """One symbol, dark on light or light on dark, any size, to MNIST style: white on black, its box scaled to fit
    20x20 and centred in 28x28, then its center of mass moved to the middle."""
    from PIL import Image  # only needed for custom images
    a = np.asarray(Image.open(path).convert("L"), np.float32) / 255
    if np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]]).mean() > 0.5:
        a = 1 - a  # light background: invert so the ink is white
    ys, xs = np.nonzero(a > 0.2)
    if not len(ys):
        raise ValueError(f"{path}: no symbol found")
    crop = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    k = 20 / max(crop.shape)
    h, w = max(1, round(crop.shape[0] * k)), max(1, round(crop.shape[1] * k))
    out = np.zeros((28, 28), np.float32)
    out[(28 - h) // 2:(28 - h) // 2 + h, (28 - w) // 2:(28 - w) // 2 + w] = np.asarray(
        Image.fromarray((crop * 255).astype(np.uint8)).resize((w, h)), np.float32) / 255
    return center_of_mass(out)


def load_custom(folder=CUSTOM):
    """Images in folder/<label>/ as (images, labels, is_test); every 5th image of each label, in file-name order,
    is held out for testing."""
    files = [(d.name, f, i % 5 == 4) for d in sorted(folder.iterdir()) if d.is_dir()
             for i, f in enumerate(sorted(f for f in d.iterdir() if f.is_file() and not f.name.startswith(".")))
             ] if folder.exists() else []
    x = np.array([load_image(f).ravel() for _, f, _ in files], np.float32).reshape(-1, 784)
    return x, [label for label, _, _ in files], np.array([t for _, _, t in files], bool)


def forward(model, x):
    h = np.maximum(0, x @ model["W1"] + model["b1"])
    z = h @ model["W2"] + model["b2"]
    e = np.exp(z - z.max(axis=1, keepdims=True))
    return h, e / e.sum(axis=1, keepdims=True)


def train(epochs=10, batch=100, lr=0.1, hidden=256, seed=0, custom=CUSTOM):
    start = time.time()
    rng = np.random.default_rng(seed)
    x, y = load_mnist("train")
    xt, yt = load_mnist("test")
    mnist_test = len(yt)
    cx, clabels, ctest = load_custom(custom)
    labels = DIGITS + sorted(set(clabels) - set(DIGITS))
    cy = np.array([labels.index(l) for l in clabels], int)
    # ponytail: each custom label is oversampled to 1000 copies shifted by up to 2 px, so a few dozen drawings aren't
    # drowned out by MNIST's ~6000 per digit; real augmentation (C10) if custom classes overfit
    for c in np.unique(cy[~ctest]):
        pick = rng.choice(np.flatnonzero((cy == c) & ~ctest), 1000)
        shifts = rng.integers(-2, 3, (1000, 2))
        copies = [np.roll(cx[i].reshape(28, 28), s, axis=(0, 1)).ravel() for i, s in zip(pick, shifts)]
        x, y = np.concatenate([x, copies]), np.concatenate([y, np.full(1000, c)])
    xt, yt = np.concatenate([xt, cx[ctest]]), np.concatenate([yt, cy[ctest]])

    n = len(labels)
    model = {
        "W1": rng.normal(0, np.sqrt(2 / 784), (784, hidden)).astype(np.float32),
        "b1": np.zeros(hidden, np.float32),
        "W2": rng.normal(0, np.sqrt(2 / hidden), (hidden, n)).astype(np.float32),
        "b2": np.zeros(n, np.float32),
    }
    history = []
    for epoch in range(epochs):
        order = rng.permutation(len(x))
        for i in range(0, len(x), batch):
            xb, yb = x[order[i:i + batch]], y[order[i:i + batch]]
            h, p = forward(model, xb)
            dz = p
            dz[np.arange(len(yb)), yb] -= 1  # softmax + cross-entropy gradient
            dz /= len(yb)
            dh = (dz @ model["W2"].T) * (h > 0)
            model["W2"] -= lr * h.T @ dz
            model["b2"] -= lr * dz.sum(axis=0)
            model["W1"] -= lr * xb.T @ dh
            model["b1"] -= lr * dh.sum(axis=0)
        acc = {"train": float((forward(model, x)[1].argmax(axis=1) == y).mean()),
               "test": float((forward(model, xt)[1].argmax(axis=1) == yt).mean())}
        history.append(acc)
        print(f"epoch {epoch + 1}: train {acc['train']:.4f}, test {acc['test']:.4f}")

    pred = forward(model, xt)[1].argmax(axis=1)
    confusion = np.zeros((n, n), int)
    np.add.at(confusion, (yt, pred), 1)
    counts = {}  # label -> [train, test] custom images
    for l, t in zip(clabels, ctest):
        counts.setdefault(l, [0, 0])[t] += 1
    model["info"] = {
        "labels": labels, "layers": [784, hidden, n], "epochs": epochs, "batch": batch, "lr": lr, "seed": seed,
        "train_size": len(y), "test_size": len(yt), "mnist_train": 60000, "mnist_test": mnist_test,
        "mnist_test_accuracy": float((pred[:mnist_test] == yt[:mnist_test]).mean()),
        "custom": counts,
        "history": history, "confusion": confusion.tolist(),
        "seconds": round(time.time() - start, 1), "trained_at": time.strftime("%Y-%m-%d %H:%M"),
    }
    return model


if __name__ == "__main__":
    root = Path(__file__).parent
    config = tomllib.loads((root / "config.toml").read_text())
    model = train()
    info = model.pop("info")
    assert info["mnist_test_accuracy"] > 0.97, "training went wrong"
    np.savez(root / config["server"]["model"], **model, info=np.array(json.dumps(info)))
    print("saved", config["server"]["model"])
