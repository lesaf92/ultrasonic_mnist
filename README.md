# Ultrasonic MNIST

Digits drawn in the air: two ultrasonic sensors on an ESP32 track a point, the computer draws its trail live in a web page, and a neural network trained from scratch names the digit.

## Documentation

| File | What it holds |
|---|---|
| [docs/plan.md](docs/plan.md) | Objectives, their status, and candidate ideas waiting for approval |
| [plan-recipe.md](plan-recipe.md) | How the plan is built and kept up to date |
| [config.toml](config.toml) | Main parameters: area size, pencil and trail width, inference timeout, server |

## Run

Needs Python 3.11+ and NumPy.

```sh
python3 train.py        # downloads MNIST to data/, trains the network, writes model.npz (~15 s)
python3 server.py       # then open http://127.0.0.1:8000
python3 test_server.py  # self-check of /predict and /config
```

The **Mouse** tab: draw a digit; it is read `timeout_s` seconds after the first point. The **ESP32** tab will show the sensor trail once the board streams data.

## Brief

The owner's description of the project, 2026-10-28:

> The main objective of this project is to create a handwritten number recognition app that uses two ultrasonic sensors to capture a point in 2D space, that point leaves a trail that draws the number in a web interface and a neural network trained from scratch is used to identify the number written in a 3 to 5 seconds trail. The two ultrasonic sensors can be plugged to a ESP32 board that sends data to the computer via WiFi and the computer shows the trail in realtime, then, after a fixed-configurable timeout, a neural network that has been trained in the MNIST dataset, or equivalent, is inferred to identify the number.
