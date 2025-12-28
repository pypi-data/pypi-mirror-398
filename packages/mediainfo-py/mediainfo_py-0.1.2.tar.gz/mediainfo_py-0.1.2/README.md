# mediainfo-py

`mediainfo-py` is a lightweight Python package for extracting video metadata using FFmpeg.
It provides a simple, Pythonic interface to retrieve commonly needed information such as
resolution, frame rate (FPS), codec, and duration.

---

## Package Information

- **Package name:** mediainfo-py  
- **Current version:** 0.1.1  
- **Author:** Aditya Katyal  
- **Country:** India  
- **License:** MIT  

---

## What this package does

This package wraps FFmpeg’s `ffprobe` functionality and exposes it as a reusable Python class.

You can use it to:
- Get video resolution (width × height)
- Extract frame rate (FPS)
- Identify video codec
- Get total media duration

It is designed to be simple, predictable, and reusable across projects such as:
- media downloaders
- video processing pipelines
- analysis tools
- automation scripts

---

## Installation

Install from PyPI using pip:

```bash
pip install mediainfo-py
