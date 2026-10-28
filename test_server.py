"""Run: python3 test_server.py (needs model.npz from train.py)."""
import json
import threading
import urllib.error
import urllib.request

import numpy as np

from server import make_server
from train import load_mnist

server = make_server("127.0.0.1", 0)
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
    hits += out["digit"] == label
assert hits >= 190, hits

for bad in ({"pixels": [0] * 783}, {"pixels": ["a"] * 784}, {"nope": 1}, [1, 2]):
    assert post(bad)[0] == 400, bad

assert json.load(urllib.request.urlopen(base + "/config"))["area"]["width"] > 0
assert b"<canvas" in urllib.request.urlopen(base + "/").read()
print(f"ok: {hits}/200 shifted test digits read correctly")
