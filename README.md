# 🖱️ Python Auto Clicker & Macro Recorder

<div align="center">
  <p>A simple, command-line based Python script to precisely record and replay mouse and keyboard actions.</p>
</div>

---

## 🌟 Features

- **Simple CLI**: Easy commands to start recording or playing back macros.
- **Accurate Playback**: Captures time deltas to recreate actions with exact timing.
- **Raw Array Output**: Prints the formatted array of events directly to the terminal.
- **State Persistence**: Saves the recorded macro locally (`macro.pkl`) so you can play it back anytime.
- **Cross-Platform**: Built on top of `pynput` for cross-platform compatibility (macOS, Linux, Windows).

## 🚀 Getting Started

### Prerequisites

This script requires Python 3 and the `pynput` library.

Install the required dependencies using the `requirements.txt` file:
```bash
pip install -r requirements.txt
```
*(Alternatively, you can just run `pip install pynput`)*

### Usage

Navigate to the project directory and run the script using the following commands:

#### 1. Record a Macro

To start recording your actions:
```bash
python3 auto_clicker.py record
```
- The script will begin recording instantly.
- Move your mouse, click, scroll, and type.
- Press the **`[ESC]`** key to stop recording.
- The recorded events will be printed to your terminal and saved to a `macro.pkl` file in the same directory.

#### 2. Play a Macro

To play back the actions you just recorded:
```bash
python3 auto_clicker.py play
```
- The script will automatically load the saved `macro.pkl`.
- You will have a **3-second countdown** before playback begins, allowing you to position your mouse or switch windows.
- It will precisely replicate all your saved mouse and keyboard events with their original timing.

## 🛠️ How it Works

The script captures every mouse and keyboard event and stores them as an array of tuples in the format: `(event_type, target_time, data)`. 
- `target_time` is the relative time from the start of the recording, ensuring perfect playback synchronization.
- When saving, this array is serialized using Python's `pickle` module into `macro.pkl`.

## ⚠️ Troubleshooting

- **Mac Users:** If the script doesn't seem to record your mouse or keyboard, ensure that your Terminal application has "Accessibility" permissions enabled in `System Settings -> Privacy & Security -> Accessibility`.
- **Linux Users:** If you get permission errors or if the listener fails, run the script with `sudo`:
  ```bash
  sudo python3 auto_clicker.py record
  ```
