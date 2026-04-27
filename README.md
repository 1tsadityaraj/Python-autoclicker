# 🖱️ Python Auto Clicker

A sleek, modern auto clicker built with Python, tkinter, and pynput.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

## Features

- ⏱️ **Precise Interval Control** — Set click intervals in hours, minutes, seconds, and milliseconds
- 🖱️ **Mouse Button Selection** — Choose between Left, Right, or Middle mouse button
- 🔁 **Click Type** — Single or Double click support
- ⌨️ **F6 Hotkey** — Toggle auto-clicking on/off from anywhere
- 🎨 **Modern Dark UI** — Beautiful, intuitive interface with smooth animations
- 📊 **Live Stats** — Real-time click counter and session timer

## Installation

```bash
# Clone the repository
git clone https://github.com/1tsadityaraj/Python-autoclicker.git
cd Python-autoclicker

# Install dependencies
pip install -r requirements.txt

# Run the application
python auto_clicker.py
```

## Usage

1. **Set the click interval** using the hours, minutes, seconds, and milliseconds fields
2. **Choose the mouse button** (Left, Right, or Middle)
3. **Select the click type** (Single or Double)
4. **Press F6** or click the Start/Stop button to toggle auto-clicking

## Troubleshooting

### macOS
- Grant **Accessibility** permissions to your terminal/IDE in **System Preferences → Privacy & Security → Accessibility**

### Linux
- Run with `sudo` if hotkeys don't work:
  ```bash
  sudo python auto_clicker.py
  ```
- Or add yourself to the `input` group:
  ```bash
  sudo usermod -aG input $USER
  ```
  Then log out and log back in.

### Windows
- Run as **Administrator** if hotkeys aren't responding

## License

MIT License — free to use, modify, and distribute.
