"""Run: python3 test_server.py (needs model.npz from train.py)."""
import json
import socket
import tempfile
import threading
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from server import CONFIG, make_server, to_area
from train import load_custom, load_mnist

server = make_server("127.0.0.1", 0, 0)
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{server.server_port}"


def post(body):
    try:
        with urllib.request.urlopen(base + "/predict", json.dumps(body).encode()) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.load(e)


x, y = load_mnist("test")
hits = 0
for img, label in zip(x[:200], y[:200]):
    off_center = np.roll(img.reshape(28, 28), (3, -3), axis=(0, 1))  # center_of_mass must undo this
    status, out = post({"pixels": off_center.ravel().tolist()})
    assert status == 200 and abs(sum(out["probs"]) - 1) < 1e-3
    hits += out["label"] == str(label)
assert hits >= 190, hits

for bad in ({"pixels": [0] * 783}, {"pixels": ["a"] * 784}, {"nope": 1}, [1, 2], {"pixels": [float("nan")] * 784}):
    assert post(bad)[0] == 400, bad

# Custom images: dark "+" of any size and place on white become MNIST-style 28x28, every 5th held out for testing
custom = Path(tempfile.mkdtemp())
(custom / "plus").mkdir()
for i in range(5):
    im = Image.new("L", (200, 150), 255)
    s, cx, cy = 20 + 15 * i, 40 + 25 * i, 70
    ImageDraw.Draw(im).line([(cx - s, cy), (cx + s, cy)], 0, 8)
    ImageDraw.Draw(im).line([(cx, cy - s), (cx, cy + s)], 0, 8)
    im.save(custom / "plus" / f"{i}.png")
cx_, clabels, ctest = load_custom(custom)
assert clabels == ["plus"] * 5 and ctest.tolist() == [False] * 4 + [True]
for img in cx_.reshape(-1, 28, 28):
    ys, xs = np.nonzero(img > 0.2)
    assert img.max() > 0.9 and img[0].max() == 0 and max(np.ptp(ys), np.ptp(xs)) <= 20
    assert abs((np.indices(img.shape)[0] * img).sum() / img.sum() - 13.5) <= 0.5

# ESP32: a UDP packet reaches an open /stream as an event with the point on the area
(x0, x1), (y0, y1) = CONFIG["esp32"]["x_mm"], CONFIG["esp32"]["y_mm"]
assert to_area(x0, y0) == [0, 0] and to_area(x1, y1) == [CONFIG["area"]["width"], CONFIG["area"]["height"]]
assert to_area(-1, y0) is None and to_area(x1 + (x1 - x0), y0) is None
stream = urllib.request.urlopen(base + "/stream")
udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
for packet in (b"garbage", b"1 2 3", f"{x0} -1".encode(), f"{x0} {y1}".encode()):
    udp.sendto(packet, ("127.0.0.1", server.udp.getsockname()[1]))
events = [json.loads(stream.readline().removeprefix(b"data: ") + stream.readline()) for _ in range(2)]
assert events == [{"d": [x0, -1], "p": None}, {"d": [x0, y1], "p": [0, CONFIG["area"]["height"]]}], events

info = json.load(urllib.request.urlopen(base + "/model"))
assert info["labels"][:10] == [str(d) for d in range(10)] and len(info["history"]) == info["epochs"]
assert json.load(urllib.request.urlopen(base + "/config"))["area"]["width"] > 0
page = urllib.request.urlopen(base + "/")
assert b"<canvas" in page.read() and page.headers["Cache-Control"] == "no-cache"
print(f"ok: {hits}/200 shifted test digits read correctly")
