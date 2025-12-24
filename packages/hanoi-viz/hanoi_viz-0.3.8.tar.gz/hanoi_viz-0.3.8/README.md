# 🗼 Towers of Hanoi

![PyPI - Version](https://img.shields.io/pypi/v/hanoi-viz)
![PyPI - License](https://img.shields.io/pypi/l/hanoi-viz)
[![CI status](https://github.com/eytanohana/Hanoi/actions/workflows/ci.yml/badge.svg)](https://github.com/eytanohana/Hanoi/actions/workflows/ci.yml)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/hanoi-viz)


A small Python project that **visualizes the Towers of Hanoi puzzle**
using **pygame** for animation and **rich** for colorful CLI output.

**Towers of Hanoi** is a fun game consisting of three pegs on a board  with a stack of different sized discs.
The game starts with the discs stacked from largest to smallest on the first peg.
The objective is to move the entire stack from the first peg to the third peg.

The rules are simple:
1. You can only move a single disk at a time.
2. You can only move the top disc of a stack to any other stack or empty peg.
3. You can't place a larger disc on top of a smaller one.

![Hanoi Animation](static/hanoi.gif)

The game quickly increases in difficulty as the number of discs used to play grows.
In fact, the game can be played with an arbitrary amount of discs.

------------------------------------------------------------------------

## ✨ Features

-   Smooth animated visualization of the Towers of Hanoi algorithm
-   Generator-based Hanoi solver (clean separation of logic vs rendering)
-   Colorful, styled CLI output using `rich`
-   Adjustable number of disks and animation speed
-   Clean shutdown handling (window close, Ctrl+C)

------------------------------------------------------------------------

## 📦 Requirements

-   Python **3.8+**
-   [`uv`](https://github.com/astral-sh/uv)
-   `pygame`
-   `rich`

All dependencies are managed via **uv**.

------------------------------------------------------------------------

## 🚀 Getting Started

### 1️⃣ Clone the repository

``` bash
git clone https://github.com/eytanohana/Hanoi.git
cd Hanoi
```

### 2️⃣ Run the game

``` bash
uv run hanoi-viz
```

------------------------------------------------------------------------

## 🎮 Usage

``` bash
uv run hanoi-viz [n_disks] [--speed SPEED]
```

### Arguments
``` bash
uv run hanoi-viz --help
```

| Argument  | Description                                     | Default |
|-----------|-------------------------------------------------|---------|
| `n_disks` | Number of disks (1–15)                          | `3`     |
| `--speed` | Pixels moved per frame (animation speed, >= 10) | `15`    |

### Examples

``` bash
uv run hanoi-viz
uv run hanoi-viz 5
uv run hanoi-viz 6 --speed 25
```

------------------------------------------------------------------------

## 🧠 How It Works

-   The **Hanoi solver** is implemented as a Python generator (`hanoi()`).
-   Each yielded move `(disc, from_peg, to_peg)` is animated in pygame.
-   Disks are lifted, slid horizontally, and dropped with smooth per-frame motion.
-   The game loop remains responsive at all times.

------------------------------------------------------------------------

## 🛑 Exiting the Game

-   Close the pygame window, or
-   Press **Ctrl+C** in the terminal

Both exit paths are handled cleanly.

------------------------------------------------------------------------

## 🛠 Development Notes

-   The project intentionally avoids over-packaging --- it's a focused script-based app.
-   Rich is used for readable CLI output without interfering with pygame.
-   The code is structured to be easy to refactor into a package if desired.

------------------------------------------------------------------------

## 📜 License

MIT License --- feel free to use, modify, and learn from it.

------------------------------------------------------------------------

## 🙌 Credits

Built with: - 🐍 Python - 🎮 pygame - 🌈 rich - ⚡ uv

Enjoy watching recursion come to life!
