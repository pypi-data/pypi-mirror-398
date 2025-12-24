# ⌨️🖱️ Pymousekey

A python package for handling keyboard and mouse inputs

---

## 📖 Description

Pymousekey offers a range of functions to interact with the operating system by sending various mouse and keyboard inputs, making it useful for automation, testing, and scripting repetitive tasks.

---

## 🧩 Requirements
- Python 3.8+ (may work on earlier Python 3 versions)
- Windows operating system

---

## ⚙️ Installation

```bash
pip install pymousekey
```
## 🚀 Example Usage

```python
import pymousekey

# Left click at a position
pymousekey.click(255, 720, button='left')

# Right click at a position
pymousekey.click(255, 720, button='right')

# Left click at multiple locations without delay
pymousekey.click(0, 500, _pause=False)
pymousekey.click(800, 200, _pause=False)
pymousekey.click(300, 900, _pause=False)

# Add a global hotkey
pymousekey.add_hotkey("numpad 5")

# Press a key
pymousekey.press("a")

# Scroll up 1 notch
pymousekey.scroll(-1)

# Scroll down 1 notch
pymousekey.scroll(1)

```