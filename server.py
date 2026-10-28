"""Serves the web page, its config, and POST /predict (784 pixels in, digit out)."""
import json
import tomllib
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np

from train import forward

ROOT = Path(__file__).parent
CONFIG = tomllib.loads((ROOT / "config.toml").read_text())


def center_of_mass(img):
    """Shift a 28x28 image so its center of mass sits in the middle, as MNIST does."""
    total = img.sum()
    if total == 0:
        return img
    ys, xs = np.indices(img.shape)
    dy, dx = round(13.5 - (ys * img).sum() / total), round(13.5 - (xs * img).sum() / total)
    return np.roll(img, (dy, dx), axis=(0, 1))


def predict(model, pixels):
    img = center_of_mass(pixels.reshape(28, 28))
    return forward(model, img.reshape(1, 784))[1][0]


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/config":
            return self.reply(200, CONFIG)
        super().do_GET()

    def do_POST(self):
        if self.path != "/predict":
            return self.reply(404, {"error": "not found"})
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length > 100_000:
                raise ValueError("body too large")
            pixels = np.asarray(json.loads(self.rfile.read(length))["pixels"], np.float32)
            if pixels.shape != (784,) or not np.isfinite(pixels).all():
                raise ValueError("pixels must be 784 numbers")
        except (ValueError, KeyError, TypeError) as e:
            return self.reply(400, {"error": str(e)})
        probs = predict(self.server.model, pixels)
        self.reply(200, {"digit": int(probs.argmax()), "probs": probs.round(4).tolist()})

    def reply(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def make_server(host, port):
    server = ThreadingHTTPServer((host, port), partial(Handler, directory=str(ROOT / "web")))
    server.model = dict(np.load(ROOT / CONFIG["server"]["model"]))
    return server


if __name__ == "__main__":
    host, port = CONFIG["server"]["host"], CONFIG["server"]["port"]
    print(f"http://{host}:{port}")
    make_server(host, port).serve_forever()
