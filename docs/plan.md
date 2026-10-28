# Plan

This file tracks the project's objectives: main quests that build the system, side quests that are tangents, and candidate ideas. Each finished objective gets its pull request or commit in the Git column; check one with `git show --stat <commit>`. The folder is not a git repository yet, so that column is empty for now.

Candidates stay **Not confirmed** until the owner approves one or asks for it to be worked on. It then moves up as a main or side quest with the next free number and notes its old one ("was C7"). The file is kept up to date as [the recipe](../plan-recipe.md#keeping-it-up-to-date-every-later-session) describes.

**Big picture:** an ESP32 with two ultrasonic sensors tracks a point in 2D space and streams it over WiFi to a computer, whose web page draws the point's trail live and, after a configurable 3–5 s timeout, names the digit drawn using a neural network trained from scratch on MNIST or an equivalent dataset.

**Now:** the last objectives finished are S1 (Mouse tab) and M7 (config file), not committed, 2026-10-28. The next one is not chosen yet; M1 and M2 (the ESP32 side) finish M3 and M6, and wait on C1 and C2.

## Main quests

Objectives that lead to the big picture, in the planned order. M1–M6 come from the [brief](../README.md#brief).

| # | Objective | Status | Git | Documentation |
|---|---|---|---|---|
| M1 | Two ultrasonic sensors on an ESP32 give one (x, y) point inside a drawing area | Open | — | — |
| M2 | The ESP32 streams the points to the computer over WiFi | Open | — | — |
| M3 | A web page on the computer draws the trail in real time | Partly done: page with Mouse and ESP32 tabs; the ESP32 tab waits on M2 | — | [README: run](../README.md#run) |
| M4 | A trail ends after a fixed, configurable timeout (3–5 s) and becomes one digit drawing | Done; the timeout counts from the first point (C6 asks if that is right) | — | [config](../config.toml) |
| M5 | A neural network trained from scratch on MNIST, or an equivalent dataset | Partly done: C8 and C9 wait on owner | — | — |
| M5.1 | NumPy 784-256-10 network trained from random weights on MNIST (`train.py`), 97.5% test accuracy | Done | — | [README: run](../README.md#run) |
| M6 | The network names the digit in a finished trail, shown on the web page | Partly done: works in the Mouse tab; the ESP32 tab waits on M2 | — | — |
| M6.1 | Turn the trail into an MNIST-style 28×28 image (centred, scaled, stroke width) | Done | — | — |
| M6.2 | Run inference on that image (`POST /predict`) and show the digit and all ten probabilities | Done | — | — |
| M7 | `config.toml` sets the main parameters: area size, pencil and trail width, timeout, network stroke width, server | Done | — | [config](../config.toml) |

## Side quests

Tangents such as tooling, simulators or viewers. S1 feeds M3, M4 and M6.

| # | Objective | Status | Git | Documentation |
|---|---|---|---|---|
| S1 | Mouse tab: draw with the mouse to test trail, timeout and inference without hardware (was C12, mouse part) | Done | — | [README: run](../README.md#run) |

## Candidates (not confirmed)

Grouped by the objective each one would serve. "Came from" points to where the idea was written down; "Planning" means the agent raised it while this plan was first written, 2026-10-28.

| # | Candidate | Serves | Came from | Status |
|---|---|---|---|---|
| | **Sensor rig** | | | |
| C1 | Mounting geometry: two sensors on one baseline with the point found by trilateration, or at right angles with one axis each | M1 | Planning | Not confirmed, waits on owner |
| C2 | Sensor model: HC-SR04 runs at 5 V and needs a divider on its echo pin for the ESP32; a 3.3 V part (HC-SR04P, RCWL-1601) does not | M1 | Planning | Not confirmed, waits on owner |
| C3 | Fire the two sensors in turn so their pings don't cross; this caps the rate near 10–20 points/s | M1, M3 | Planning | Not confirmed |
| C4 | Calibration knobs (baseline, sensor offsets, drawing-area bounds) settable without reflashing | M1 | Planning | Not confirmed |
| C5 | Smooth noisy readings: median of a few pings, drop out-of-range jumps | M1, M6 | Planning | Not confirmed |
| | **Trail capture** | | | |
| C6 | The timeout counts from a trail's first point (as built in M4); the alternative is counting from the last movement | M4 | [Brief](../README.md#brief): "after a fixed-configurable timeout" | Not confirmed, waits on owner |
| C7 | Pen-up: moving out of range splits the trail into strokes, so two-stroke digits (4, 5) don't gain a joining line | M4, M6 | Planning | Not confirmed |
| | **Network** | | | |
| C13 | Show "?" when the top probability is low: any scribble is read as some digit (a straight diagonal read as 5 at 44%) | M6 | Testing S1, 2026-10-28 | Not confirmed |
| C8 | What "from scratch" means: own NumPy network and training loop (as built in M5.1), or a framework (PyTorch) trained from random weights | M5 | [Brief](../README.md#brief): "trained from scratch" | Not confirmed, waits on owner |
| C9 | Dataset: MNIST (as used in M5.1), or EMNIST Digits (same 28×28 format, 240k training images) | M5 | [Brief](../README.md#brief): "MNIST dataset, or equivalent" | Not confirmed, waits on owner |
| C10 | Train with augmentation (jitter, rotation, stroke width) so wobbly ultrasonic trails look less unlike pen digits | M5, M6 | Planning | Not confirmed |
| C11 | Record labelled trails from the rig, to measure real accuracy and fine-tune if MNIST alone falls short | M5, M6 | Planning | Not confirmed |
| | **Building without hardware** | | | |
| C12 | Replay recorded trails through the ESP32 tab as a fake ESP32 (the mouse part became S1) | M3, M4, M6 | Planning | Not confirmed |
