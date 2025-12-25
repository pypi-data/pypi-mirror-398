# tapoapi

Unofficial Python client for controlling **TP-Link Tapo cameras over the local network**, without the official Tapo app.

This project is **not affiliated with TP-Link**.

> This started as a small personal reverse‑engineering project. I’m publishing it in case others find it useful. It’s provided **as‑is** and may not be actively maintained.

---

## Features

* Camera movement (pan/tilt)
* Nothing else… yet!

---

## Compatibility

| Model      | Firmware | Status        |
| ---------- | -------: | ------------- |
| Tapo C200C |    1.3.1 | Fully working |

> ⚠️ Other models and firmware versions may work partially or not at all.

---

## Installation

```bash
pip install tapoapi
```

---

## Quick start

```python
from tapoapi import Camera

cam = Camera(
    "192.168.1.115",
    username="admin",
    password="YOUR_CAMERA_PASSWORD"
)

# Move the camera relatively (pan, tilt)
cam.relative_move(0, 10)
```

## Development & building

```bash
python -m pip install -U build
python -m build
```

---

## Disclaimer

This software is provided for **educational and research purposes**. Use at your own risk. Firmware updates may break functionality at any time.