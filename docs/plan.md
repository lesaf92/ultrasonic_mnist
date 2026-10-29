# Plan

This file tracks the project's objectives: main quests that build the system, side quests that are tangents, and candidate ideas. Each finished objective gets its pull request or commit in the Git column; check one with `git show --stat <commit>`. Everything built before the repository existed landed in its first commit, e9c1862.

Candidates stay **Not confirmed** until the owner approves one or asks for it to be worked on. It then moves up as a main or side quest with the next free number and notes its old one ("was C7"). The file is kept up to date as [the recipe](../plan-recipe.md#keeping-it-up-to-date-every-later-session) describes.

**Big picture:** an ESP32 with two ultrasonic sensors tracks a point in 2D space and streams it over WiFi to a computer, whose web page draws the point's trail live and, after a configurable 3–5 s timeout, names the digit drawn using a neural network trained from scratch on MNIST or an equivalent dataset.

**Now:** M2 is the objective being worked on, 2026-10-29: the firmware compiles and the server relays its UDP packets to the ESP32 tab (tested with a fake sender); next is flashing the board and testing with the sensors. S2 and S3 are done. All of it is in 18c1583. C1 (mounting) still waits on the owner.

## Main quests

Objectives that lead to the big picture, in the planned order. M1–M6 come from the [brief](../README.md#brief).

| # | Objective | Status | Git | Documentation |
|---|---|---|---|---|
| M1 | Two ultrasonic sensors on an ESP32 give one (x, y) point inside a drawing area | Partly done: the firmware reads both HC-SR04s; until C1 is chosen each sensor gives one axis, with its range in `config.toml`; left: test on the rig | 18c1583, 2026-10-29 | [README: ESP32](../README.md#esp32), [config](../config.toml) |
| M2 | The ESP32 streams the points to the computer over WiFi | Partly done: firmware sends each reading as a UDP packet, `server.py` relays it to the page on `/stream`; left: flash the board and test it | 18c1583, 2026-10-29 | [README: ESP32](../README.md#esp32), [firmware settings](../firmware/config.example.h) |
| M3 | A web page on the computer draws the trail in real time | Partly done: page with Mouse and ESP32 tabs; the ESP32 tab draws streamed points (tested with a fake sender) and waits on M2's board test | e9c1862, 2026-10-28 | [README: run](../README.md#run) |
| M4 | A trail ends after a fixed, configurable timeout (3–5 s) and becomes one digit drawing | Done; the timeout counts from the first point (C6 asks if that is right) | e9c1862, 2026-10-28 | [config](../config.toml) |
| M5 | A neural network trained from scratch on MNIST, or an equivalent dataset | Partly done: C8 and C9 wait on owner | e9c1862, 2026-10-28 | — |
| M5.1 | NumPy 784-256-10 network trained from random weights on MNIST (`train.py`), 97.5% test accuracy | Done | e9c1862, 2026-10-28 | [README: run](../README.md#run), [Model tab](../web/index.html) |
| M6 | The network names the digit in a finished trail, shown on the web page | Partly done: works in the Mouse tab, and in the ESP32 tab with a fake sender; waits on M2's board test | e9c1862, 2026-10-28 | — |
| M6.1 | Turn the trail into an MNIST-style 28×28 image (centred, scaled, stroke width) | Done | e9c1862, 2026-10-28 | [Model tab: from trail to input](../web/index.html) |
| M6.2 | Run inference on that image (`POST /predict`) and show the digit and all ten probabilities | Done | e9c1862, 2026-10-28 | — |
| M7 | `config.toml` sets the main parameters: area size, pencil and trail width, timeout, network stroke width, server | Done | e9c1862, 2026-10-28 | [config](../config.toml) |

## Side quests

Tangents such as tooling, simulators, viewers or teaching material. S1 feeds M3, M4 and M6; S2 explains M5 and M6; S3 feeds M5 and covers part of C11.

| # | Objective | Status | Git | Documentation |
|---|---|---|---|---|
| S1 | Mouse tab: draw with the mouse to test trail, timeout and inference without hardware (was C12, mouse part) | Done | e9c1862, 2026-10-28 | [README: run](../README.md#run) |
| S2 | Model tab: architecture, per-epoch accuracy, confusion matrix, dataset source, trail-to-input steps; read from the model file so it follows each retraining | Done | 18c1583, 2026-10-29 | [Model tab](../web/index.html) |
| S3 | Custom labels: images copied into `data/custom/<label>/` are made MNIST-style by `train.py` and added as extra outputs; the page itself never records or trains | Done | 18c1583, 2026-10-29 | [Model tab: train your own symbol](../web/index.html), [README: run](../README.md#run) |

## Candidates (not confirmed)

Grouped by the objective each one would serve. "Came from" points to where the idea was written down; "Planning" means the agent raised it while this plan was first written, 2026-10-28.

| # | Candidate | Serves | Came from | Status |
|---|---|---|---|---|
| | **Sensor rig** | | | |
| C1 | Mounting geometry: two sensors on one baseline with the point found by trilateration, or at right angles with one axis each | M1 | Planning | Not confirmed, waits on owner |
| C2 | Sensor model: HC-SR04 runs at 5 V and needs a divider on its echo pin for the ESP32; a 3.3 V part (HC-SR04P, RCWL-1601) does not | M1 | Planning | Done: the owner chose HC-SR04, 2026-10-29; the divider is in [README: ESP32](../README.md#esp32) |
| C3 | Fire the two sensors in turn so their pings don't cross; this caps the rate near 10–20 points/s | M1, M3 | Planning | Done in M2: A then B, 25 ms apart (`PING_GAP_MS`), ~17 points/s |
| C4 | Calibration knobs (baseline, sensor offsets, drawing-area bounds) settable without reflashing | M1 | Planning | Partly done in M2: the area bounds are the `[esp32]` ranges in `config.toml`; left: baseline and offsets, which depend on C1 |
| C5 | Smooth noisy readings: median of a few pings, drop out-of-range jumps | M1, M6 | Planning | Not confirmed |
| C15 | Find the computer without its IP in `firmware/config.h` (mDNS name or UDP broadcast), so a new DHCP address doesn't need a reflash | M2 | Building M2, 2026-10-29 | Not confirmed |
| | **Trail capture** | | | |
| C6 | The timeout counts from a trail's first point (as built in M4); the alternative is counting from the last movement | M4 | [Brief](../README.md#brief): "after a fixed-configurable timeout" | Not confirmed, waits on owner |
| C7 | Pen-up: moving out of range splits the trail into strokes, so two-stroke digits (4, 5) don't gain a joining line | M4, M6 | Planning | Not confirmed |
| | **Network** | | | |
| C13 | Show "?" when the top probability is low: any scribble is read as some digit (a straight diagonal read as 5 at 44%) | M6 | Testing S1, 2026-10-28 | Not confirmed |
| C8 | What "from scratch" means: own NumPy network and training loop (as built in M5.1), or a framework (PyTorch) trained from random weights | M5 | [Brief](../README.md#brief): "trained from scratch" | Not confirmed, waits on owner |
| C9 | Dataset: MNIST (as used in M5.1), or EMNIST Digits (same 28×28 format, 240k training images) | M5 | [Brief](../README.md#brief): "MNIST dataset, or equivalent" | Not confirmed, waits on owner |
| C10 | Train with augmentation (jitter, rotation, stroke width) so wobbly ultrasonic trails look less unlike pen digits | M5, M6 | Planning | Not confirmed |
| C11 | Record labelled trails from the rig, to measure real accuracy and fine-tune if MNIST alone falls short | M5, M6 | Planning | Partly done in S3 (training from an image folder works); left: a way to save rig trails as images, needs M1 and M2 |
| C14 | Undo button for the last saved trail; today a bad one is removed by deleting its line in `data/samples.jsonl` | S3 | Building S3, 2026-10-28 | Dropped, 2026-10-29: the page no longer records trails |
| | **Building without hardware** | | | |
| C12 | Replay recorded trails through the ESP32 tab as a fake ESP32 (the mouse part became S1) | M3, M4, M6 | Planning | Not confirmed |
