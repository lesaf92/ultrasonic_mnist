"""Train a 784-256-10 MLP on MNIST with NumPy only, from random weights. Writes the model file named in config.toml."""
import gzip
import tomllib
import urllib.request
from pathlib import Path

import numpy as np

URL = "https://storage.googleapis.com/cvdf-datasets/mnist/"
DATA = Path(__file__).parent / "data"


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


def forward(model, x):
    h = np.maximum(0, x @ model["W1"] + model["b1"])
    z = h @ model["W2"] + model["b2"]
    e = np.exp(z - z.max(axis=1, keepdims=True))
    return h, e / e.sum(axis=1, keepdims=True)


def train(epochs=10, batch=100, lr=0.1, hidden=256, seed=0):
    rng = np.random.default_rng(seed)
    x, y = load_mnist("train")
    model = {
        "W1": rng.normal(0, np.sqrt(2 / 784), (784, hidden)).astype(np.float32),
        "b1": np.zeros(hidden, np.float32),
        "W2": rng.normal(0, np.sqrt(2 / hidden), (hidden, 10)).astype(np.float32),
        "b2": np.zeros(10, np.float32),
    }
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
        print(f"epoch {epoch + 1}: test accuracy {accuracy(model):.4f}")
    return model


def accuracy(model):
    x, y = load_mnist("test")
    return (forward(model, x)[1].argmax(axis=1) == y).mean()


if __name__ == "__main__":
    root = Path(__file__).parent
    config = tomllib.loads((root / "config.toml").read_text())
    model = train()
    assert accuracy(model) > 0.97, "training went wrong"
    np.savez(root / config["server"]["model"], **model)
    print("saved", config["server"]["model"])
