# Python Auto Clicker & Macro Recorder

A simple, command-line based Python script to record and replay mouse and keyboard actions. This script precisely captures mouse movements, clicks, scrolls, and key presses, and allows you to play them back instantly.

## Features
- **Simple CLI**: Easy commands to start recording or playing back macros.
- **Accurate Playback**: Captures time deltas to recreate actions with exact timing.
- **Raw Array Output**: Prints the formatted array of events directly to the terminal.
- **State Saving**: Saves the recorded macro locally so you can play it back anytime.

## Prerequisites

This script requires Python 3 and the `pynput` library.

Install the required dependency:
```bash
pip3 install pynput
```

## Usage

Navigate to the project directory and run the script using the following commands:

### 1. Record a Macro
To start recording your actions:
```bash
python3 auto_clicker.py record
```
- The script will begin recording instantly.
- Move your mouse, click, scroll, and type.
- Press the **[ESC]** key to stop recording.
- The recorded events will be printed to your terminal and saved to a `macro.pkl` file.

### 2. Play a Macro
To play back the actions you just recorded:
```bash
python3 auto_clicker.py play
```
- The script will load `macro.pkl`.
- You will have a 3-second countdown before playback begins.
- It will precisely replicate all your saved mouse and keyboard events.

## Troubleshooting
**Mac Users:** If the script doesn't seem to record your mouse or keyboard, ensure that your Terminal application has "Accessibility" permissions enabled in `System Settings -> Privacy & Security -> Accessibility`.

**Linux Users:** If you get permission errors or if the listener fails, run the script with `sudo`:
```bash
sudo python3 auto_clicker.py record
```
