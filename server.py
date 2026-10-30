"""Serves the web page, its config, the model's training results, and POST /predict (784 pixels in, label out).
Also listens for the ESP32's UDP readings and relays them to the page as server-sent events on /stream."""
import json
import queue
import socket
import threading
import tomllib
from collections import deque
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np

from train import center_of_mass, forward

ROOT = Path(__file__).parent
CONFIG = tomllib.loads((ROOT / "config.toml").read_text())


def to_area(x, y):
    """Distances in mm to a point on the drawing area in px, or None when outside it or without an echo.
    As in docs/apparatus.jpeg, x comes from the sensor on the Y axis and y from the sensor on the X axis; y grows
    upwards there and downwards on the page.
    ponytail: a reading is the distance to the object, not its coordinate, so off a sensor's axis it reads long
    (1% at the edge of a 15° beam); correct it with the sensors' positions (C16) if trails come out bent."""
    (x0, x1), (y0, y1) = CONFIG["esp32"]["x_mm"], CONFIG["esp32"]["y_mm"]
    fx, fy = (x - x0) / (x1 - x0), (y - y0) / (y1 - y0)
    if x < 0 or y < 0 or not (0 <= fx <= 1 and 0 <= fy <= 1):
        return None
    return [round(fx * CONFIG["area"]["width"], 1), round((1 - fy) * CONFIG["area"]["height"], 1)]


def parse_reading(data):
    """A UDP packet "<x mm> <y mm>" (-1 = no echo) to (x, y), or None if malformed."""
    try:
        x, y = (int(v) for v in data.decode().split())
    except ValueError:
        return None
    return x, y


class Smoother:
    """One sensor's readings: the median of the last few drops single-ping spikes and dropouts, then a low-pass
    filter (exponential moving average) evens out jitter. No echo (-1) passes through and restarts the low-pass,
    so a trail that comes back doesn't drift in from where the last one ended."""

    def __init__(self, median_of, low_pass):
        self.recent = deque(maxlen=median_of)
        self.weight = low_pass
        self.avg = None

    def __call__(self, reading):
        self.recent.append(reading)
        median = sorted(self.recent)[len(self.recent) // 2]
        if median < 0:
            self.avg = None
            return -1
        self.avg = median if self.avg is None else self.avg + self.weight * (median - self.avg)
        return round(self.avg)


def listen_udp(server):
    while True:
        reading = parse_reading(server.udp.recvfrom(64)[0])
        if reading:
            x, y = server.smooth_x(reading[0]), server.smooth_y(reading[1])
            msg = {"d": [x, y], "p": to_area(x, y)}
        for q in list(server.clients) if reading else []:
            try:
                q.put_nowait(msg)
            except queue.Full:  # a page that stopped reading
                pass


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/config":
            return self.reply(200, CONFIG)
        if self.path == "/model":
            return self.reply(200, self.server.info)
        if self.path == "/stream":
            return self.stream()
        super().do_GET()

    def stream(self):
        q = queue.Queue(100)
        self.server.clients.add(q)
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            while True:
                try:
                    self.wfile.write(f"data: {json.dumps(q.get(timeout=15))}\n\n".encode())
                except queue.Empty:
                    self.wfile.write(b": ping\n\n")  # finds out when the page is gone
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            self.server.clients.discard(q)

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
        img = center_of_mass(pixels.reshape(28, 28))
        probs = forward(self.server.model, img.reshape(1, 784))[1][0]
        self.reply(200, {"label": self.server.info["labels"][probs.argmax()], "probs": probs.round(4).tolist()})

    def end_headers(self):
        # without it the browser may reuse a cached page that no longer matches /model after an update
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def reply(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def make_server(host, port, udp_port):
    server = ThreadingHTTPServer((host, port), partial(Handler, directory=str(ROOT / "web")))
    model = dict(np.load(ROOT / CONFIG["server"]["model"]))
    if "custom" not in json.loads(str(model.get("info", "{}"))):
        raise SystemExit("model file is from an older train.py; run python3 train.py")
    server.info = json.loads(str(model.pop("info")))
    server.model = model
    server.clients = set()  # one queue per open page
    server.smooth_x, server.smooth_y = (Smoother(CONFIG["esp32"]["median_of"], CONFIG["esp32"]["low_pass"])
                                        for _ in "xy")
    server.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.udp.bind(("0.0.0.0", udp_port))  # the ESP32 is on the WiFi, not on this machine
    threading.Thread(target=listen_udp, args=(server,), daemon=True).start()
    return server


if __name__ == "__main__":
    host, port = CONFIG["server"]["host"], CONFIG["server"]["port"]
    print(f"http://{host}:{port}, ESP32 readings on UDP port {CONFIG['esp32']['udp_port']}")
    make_server(host, port, CONFIG["esp32"]["udp_port"]).serve_forever()
