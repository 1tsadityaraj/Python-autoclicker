"""
Python Auto Clicker + Macro Recorder
A modern desktop auto-clicker with macro record & playback.
F6 = toggle clicker  |  F7 = record  |  F8 = playback
"""

import threading
import time
import sys
import platform
import os
import json
from pynput.mouse import Button, Controller, Listener as MouseListener
from pynput.keyboard import Key, KeyCode, Listener as KeyboardListener, Controller as KeyboardController

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
except ImportError:
    print("Error: tkinter is not installed.")
    if platform.system() == "Linux":
        print("  sudo apt-get install python3-tk")
    elif platform.system() == "Darwin":
        print("  brew install python-tk")
    else:
        print("  Reinstall Python with tcl/tk support from python.org")
    sys.exit(1)

# ─── Colors ──────────────────────────────────────────────────────────────────────

C = {
    "bg":      "#0d1117",  "card":    "#161b22",  "input":   "#0d1117",
    "border":  "#30363d",  "bfocus":  "#58a6ff",  "text":    "#e6edf3",
    "dim":     "#8b949e",  "accent":  "#58a6ff",  "green":   "#3fb950",
    "red":     "#f85149",  "orange":  "#d29922",  "purple":  "#bc8cff",
    "yellow":  "#e3b341",
}

# ─── Macro Recorder Engine ───────────────────────────────────────────────────────

EVENT_MOUSE_MOVE = "mouse_move"
EVENT_MOUSE_CLICK = "mouse_click"
EVENT_MOUSE_SCROLL = "mouse_scroll"
EVENT_KEY_PRESS = "key_press"
EVENT_KEY_RELEASE = "key_release"

BUTTON_MAP = {Button.left: "left", Button.right: "right", Button.middle: "middle"}
BUTTON_REVERSE = {v: k for k, v in BUTTON_MAP.items()}

def _serialize_key(key):
    if isinstance(key, KeyCode):
        return {"type": "char", "value": key.char if key.char else key.vk}
    elif isinstance(key, Key):
        return {"type": "special", "value": key.name}
    return {"type": "unknown", "value": str(key)}

def _deserialize_key(data):
    if data["type"] == "char":
        if isinstance(data["value"], int):
            return KeyCode.from_vk(data["value"])
        return KeyCode.from_char(data["value"])
    elif data["type"] == "special":
        return Key[data["value"]]
    return None

class MacroRecorder:
    def __init__(self):
        self.events = []
        self.recording = False
        self.playing = False
        self.play_thread = None
        self._mouse_listener = None
        self._keyboard_listener = None
        self._start_time = 0

        self.mouse_ctrl = Controller()
        self.keyboard_ctrl = KeyboardController()

        self.on_event_recorded = None
        self.on_playback_done = None
        self.on_playback_event = None
        self.on_recording_stopped = None

        self.record_mouse_moves = True
        self.move_sample_interval = 0.01
        self._last_move_time = 0
        self.loop_count = 1
        self.playback_speed = 1.0

    def start_recording(self):
        if self.recording: return
        self.events = []
        self.recording = True
        self._start_time = time.time()
        self._last_move_time = 0

        self._mouse_listener = MouseListener(on_move=self._on_move, on_click=self._on_click, on_scroll=self._on_scroll)
        self._keyboard_listener = KeyboardListener(on_press=self._on_key_press, on_release=self._on_key_release)
        self._mouse_listener.start()
        self._keyboard_listener.start()

    def stop_recording(self):
        if not self.recording: return
        self.recording = False
        if self._mouse_listener: self._mouse_listener.stop()
        if self._keyboard_listener: self._keyboard_listener.stop()
        if self.on_recording_stopped: self.on_recording_stopped()

    def _elapsed(self):
        return time.time() - self._start_time

    def _record(self, event):
        self.events.append(event)
        if self.on_event_recorded: self.on_event_recorded(len(self.events))

    def _on_move(self, x, y):
        if not self.recording or not self.record_mouse_moves: return
        now = self._elapsed()
        if now - self._last_move_time < self.move_sample_interval: return
        self._last_move_time = now
        self._record({"t": now, "type": EVENT_MOUSE_MOVE, "x": x, "y": y})

    def _on_click(self, x, y, button, pressed):
        if not self.recording: return
        self._record({"t": self._elapsed(), "type": EVENT_MOUSE_CLICK, "x": x, "y": y, "button": BUTTON_MAP.get(button, "left"), "pressed": pressed})

    def _on_scroll(self, x, y, dx, dy):
        if not self.recording: return
        self._record({"t": self._elapsed(), "type": EVENT_MOUSE_SCROLL, "x": x, "y": y, "dx": dx, "dy": dy})

    def _on_key_press(self, key):
        if not self.recording: return
        if key == Key.esc:
            threading.Thread(target=self.stop_recording).start()
            return False
        self._record({"t": self._elapsed(), "type": EVENT_KEY_PRESS, "key": _serialize_key(key)})

    def _on_key_release(self, key):
        if not self.recording: return
        if key != Key.esc:
            self._record({"t": self._elapsed(), "type": EVENT_KEY_RELEASE, "key": _serialize_key(key)})

    def start_playback(self):
        if self.playing or not self.events: return
        self.playing = True
        self.play_thread = threading.Thread(target=self._playback_loop, daemon=True)
        self.play_thread.start()

    def stop_playback(self):
        self.playing = False

    def _playback_loop(self):
        loops = 0
        total = len(self.events)
        while self.playing:
            start = time.time()
            for i, event in enumerate(self.events):
                if not self.playing: break
                target = event["t"] / self.playback_speed
                elapsed = time.time() - start
                wait = target - elapsed
                if wait > 0: time.sleep(wait)
                if not self.playing: break
                self._execute_event(event)
                if self.on_playback_event: self.on_playback_event(i + 1, total)
            loops += 1
            if self.loop_count > 0 and loops >= self.loop_count: break
        self.playing = False
        if self.on_playback_done: self.on_playback_done()

    def _execute_event(self, event):
        t = event["type"]
        try:
            if t == EVENT_MOUSE_MOVE:
                self.mouse_ctrl.position = (event["x"], event["y"])
            elif t == EVENT_MOUSE_CLICK:
                self.mouse_ctrl.position = (event["x"], event["y"])
                btn = BUTTON_REVERSE.get(event["button"], Button.left)
                if event["pressed"]: self.mouse_ctrl.press(btn)
                else: self.mouse_ctrl.release(btn)
            elif t == EVENT_MOUSE_SCROLL:
                self.mouse_ctrl.position = (event["x"], event["y"])
                self.mouse_ctrl.scroll(event["dx"], event["dy"])
            elif t == EVENT_KEY_PRESS:
                key = _deserialize_key(event["key"])
                if key: self.keyboard_ctrl.press(key)
            elif t == EVENT_KEY_RELEASE:
                key = _deserialize_key(event["key"])
                if key: self.keyboard_ctrl.release(key)
        except Exception:
            pass

    def save(self, filepath):
        with open(filepath, "w") as f:
            json.dump({"version": 1, "events": self.events}, f)

    def load(self, filepath):
        with open(filepath, "r") as f:
            data = json.load(f)
        self.events = data.get("events", [])

    @property
    def duration(self):
        return self.events[-1]["t"] if self.events else 0

    @property
    def event_count(self):
        return len(self.events)

# ─── Auto Clicker Core ──────────────────────────────────────────────────────────

class AutoClicker:
    def __init__(self):
        self.mouse = Controller()
        self.running = False
        self.interval = 0.1
        self.button = Button.left
        self.click_type = "single"
        self.click_count = 0

    def set_interval(self, hours=0, minutes=0, seconds=0, milliseconds=100):
        self.interval = max(0.001, hours*3600 + minutes*60 + seconds + milliseconds/1000)

    def set_button(self, name):
        self.button = {"Left": Button.left, "Right": Button.right, "Middle": Button.middle}.get(name, Button.left)

    def set_click_type(self, t):
        self.click_type = t.lower()

    def start(self):
        if self.running: return
        self.running = True
        threading.Thread(target=self._loop, daemon=True).start()

    def stop(self):
        self.running = False

    def reset(self):
        self.click_count = 0

    def _loop(self):
        clicks = 2 if self.click_type == "double" else 1
        while self.running:
            self.mouse.click(self.button, clicks)
            self.click_count += 1
            time.sleep(self.interval)

# ─── UI Helpers ──────────────────────────────────────────────────────────────────

def make_card(parent, label=None):
    w = tk.Frame(parent, bg=C["bg"])
    w.pack(fill="x", pady=(0, 10))
    if label:
        tk.Label(w, text=label, font=("Helvetica Neue", 11, "bold"),
                 fg=C["dim"], bg=C["bg"]).pack(anchor="w", pady=(0, 6))
    card = tk.Frame(w, bg=C["card"], highlightbackground=C["border"],
                    highlightthickness=1, padx=16, pady=14)
    card.pack(fill="x")
    return card

def style_menu(menu):
    menu.config(font=("Helvetica Neue", 12), fg=C["text"], bg=C["input"],
                activeforeground=C["text"], activebackground=C["card"],
                highlightbackground=C["border"], highlightthickness=1,
                relief="flat", indicatoron=True, width=8)
    menu["menu"].config(font=("Helvetica Neue", 11), fg=C["text"], bg=C["card"],
                        activeforeground="#fff", activebackground=C["accent"], relief="flat")

def make_btn(parent, text, bg_color, command, font_size=14):
    btn = tk.Button(parent, text=text, font=("Helvetica Neue", font_size, "bold"),
                    fg="#ffffff", bg=bg_color, activeforeground="#ffffff",
                    activebackground=bg_color, relief="flat", cursor="hand2",
                    padx=16, pady=10, command=command)
    return btn

# ─── Application ─────────────────────────────────────────────────────────────────

class AutoClickerApp:
    def __init__(self):
        self.clicker = AutoClicker()
        self.recorder = MacroRecorder()
        self.session_start = None

        self.root = tk.Tk()
        self.root.title("Auto Clicker + Macro Recorder")
        self.root.geometry("460x850")
        self.root.minsize(460, 830)
        self.root.configure(bg=C["bg"])
        self.root.resizable(False, False)

        # Recorder callbacks
        self.recorder.on_event_recorded = lambda n: self.root.after(0, self._update_rec_count, n)
        self.recorder.on_playback_done = lambda: self.root.after(0, self._on_playback_done)
        self.recorder.on_playback_event = lambda i, t: self.root.after(0, self._update_play_progress, i, t)
        self.recorder.on_recording_stopped = lambda: self.root.after(0, self._sync_recording_stopped)

        self._build_ui()
        self._start_hotkey_listener()
        self._tick()

    # ── Build UI ─────────────────────────────────────────────────────────────

    def _build_ui(self):
        main = tk.Frame(self.root, bg=C["bg"])
        main.pack(fill="both", expand=True, padx=16, pady=12)

        # Header
        tk.Label(main, text="🖱️  Auto Clicker",
                 font=("Helvetica Neue", 22, "bold"),
                 fg=C["text"], bg=C["bg"]).pack(anchor="w")
        tk.Label(main, text="F6 = clicker  •  F7 = record  •  F8 = play",
                 font=("Helvetica Neue", 11), fg=C["dim"], bg=C["bg"]).pack(anchor="w", pady=(2, 12))

        # Tab bar
        tab_bar = tk.Frame(main, bg=C["bg"])
        tab_bar.pack(fill="x", pady=(0, 12))

        self.tab_btns = []
        self.tab_frames = []
        for i, name in enumerate(["⏱  Clicker", "🎬  Recorder"]):
            btn = tk.Button(tab_bar, text=name, font=("Helvetica Neue", 13, "bold"),
                            fg=C["text"], bg=C["card"], activeforeground=C["text"],
                            activebackground=C["card"], relief="flat", cursor="hand2",
                            padx=20, pady=10, command=lambda idx=i: self._switch_tab(idx))
            btn.pack(side="left", expand=True, fill="x", padx=(0, 6) if i == 0 else 0)
            self.tab_btns.append(btn)

        # Tab content container
        self.tab_container = tk.Frame(main, bg=C["bg"])
        self.tab_container.pack(fill="both", expand=True)

        # Build tabs
        self._build_clicker_tab()
        self._build_recorder_tab()
        self._switch_tab(0)

    def _switch_tab(self, idx):
        for i, f in enumerate(self.tab_frames):
            f.pack_forget()
            self.tab_btns[i].config(bg=C["card"], fg=C["dim"])
        self.tab_frames[idx].pack(fill="both", expand=True)
        self.tab_btns[idx].config(bg=C["accent"], fg="#ffffff")

    # ── Clicker Tab ──────────────────────────────────────────────────────────

    def _build_clicker_tab(self):
        frame = tk.Frame(self.tab_container, bg=C["bg"])
        self.tab_frames.append(frame)

        # Interval card
        card = make_card(frame, "CLICK INTERVAL")
        row = tk.Frame(card, bg=C["card"])
        row.pack(fill="x")
        self.interval_vars = {}
        for col, (label, default) in enumerate([("Hours","0"),("Minutes","0"),("Seconds","0"),("Ms","100")]):
            cf = tk.Frame(row, bg=C["card"])
            cf.grid(row=0, column=col, padx=(0,10) if col<3 else 0, sticky="ew")
            row.columnconfigure(col, weight=1)
            tk.Label(cf, text=label.upper(), font=("Helvetica Neue", 9),
                     fg=C["dim"], bg=C["card"]).pack(anchor="w", pady=(0,4))
            var = tk.StringVar(value=default)
            self.interval_vars[label.lower()] = var
            tk.Entry(cf, textvariable=var, font=("SF Mono", 16, "bold"), fg=C["text"],
                     bg=C["input"], insertbackground=C["accent"],
                     highlightbackground=C["border"], highlightcolor=C["bfocus"],
                     highlightthickness=1, relief="flat", width=4, justify="center").pack(fill="x")
            var.trace_add("write", lambda *_: self._sync_interval())

        # Options card
        card = make_card(frame, "OPTIONS")
        r1 = tk.Frame(card, bg=C["card"]); r1.pack(fill="x", pady=(0,12))
        tk.Label(r1, text="Mouse Button", font=("Helvetica Neue", 12),
                 fg=C["text"], bg=C["card"]).pack(side="left")
        self.button_var = tk.StringVar(value="Left")
        m = tk.OptionMenu(r1, self.button_var, "Left", "Right", "Middle")
        style_menu(m); m.pack(side="right")
        self.button_var.trace_add("write", lambda *_: self.clicker.set_button(self.button_var.get()))

        tk.Frame(card, bg=C["border"], height=1).pack(fill="x", pady=2)
        r2 = tk.Frame(card, bg=C["card"]); r2.pack(fill="x", pady=(12,0))
        tk.Label(r2, text="Click Type", font=("Helvetica Neue", 12),
                 fg=C["text"], bg=C["card"]).pack(side="left")
        self.click_type_var = tk.StringVar(value="Single")
        m2 = tk.OptionMenu(r2, self.click_type_var, "Single", "Double")
        style_menu(m2); m2.pack(side="right")
        self.click_type_var.trace_add("write", lambda *_: self.clicker.set_click_type(self.click_type_var.get()))

        # Stats card
        card = make_card(frame, "LIVE STATS")
        sr = tk.Frame(card, bg=C["card"]); sr.pack(fill="x")
        left = tk.Frame(sr, bg=C["card"]); left.pack(side="left", expand=True, fill="x")
        tk.Label(left, text="CLICKS", font=("Helvetica Neue", 9), fg=C["dim"], bg=C["card"]).pack(anchor="w")
        self.click_lbl = tk.Label(left, text="0", font=("SF Mono", 26, "bold"), fg=C["accent"], bg=C["card"])
        self.click_lbl.pack(anchor="w")
        tk.Frame(sr, bg=C["border"], width=1).pack(side="left", fill="y", padx=16)
        right = tk.Frame(sr, bg=C["card"]); right.pack(side="left", expand=True, fill="x")
        tk.Label(right, text="SESSION", font=("Helvetica Neue", 9), fg=C["dim"], bg=C["card"]).pack(anchor="w")
        self.session_lbl = tk.Label(right, text="00:00", font=("SF Mono", 26, "bold"), fg=C["purple"], bg=C["card"])
        self.session_lbl.pack(anchor="w")

        # Toggle button
        bf = tk.Frame(frame, bg=C["bg"]); bf.pack(fill="x", pady=(4,0))
        self.toggle_btn = make_btn(bf, "▶  Start Clicking", C["green"], self.toggle_clicker)
        self.toggle_btn.pack(fill="x")

        sf = tk.Frame(bf, bg=C["bg"]); sf.pack(fill="x", pady=(8,0))
        self.status_dot = tk.Label(sf, text="●", font=("Helvetica Neue", 10), fg=C["dim"], bg=C["bg"])
        self.status_dot.pack(side="left")
        self.status_lbl = tk.Label(sf, text="  Idle — press F6", font=("Helvetica Neue", 11), fg=C["dim"], bg=C["bg"])
        self.status_lbl.pack(side="left")
        make_btn(sf, "Reset", C["bg"], self._reset_stats, 10).pack(side="right")

    # ── Recorder Tab ─────────────────────────────────────────────────────────

    def _build_recorder_tab(self):
        frame = tk.Frame(self.tab_container, bg=C["bg"])
        self.tab_frames.append(frame)

        # Info
        card = make_card(frame, "MACRO RECORDER")
        tk.Label(card, text="Record your mouse & keyboard actions,\nthen replay them with exact timing.",
                 font=("Helvetica Neue", 12), fg=C["text"], bg=C["card"],
                 justify="left").pack(anchor="w")

        # Settings card
        card = make_card(frame, "SETTINGS")

        r1 = tk.Frame(card, bg=C["card"]); r1.pack(fill="x", pady=(0,10))
        tk.Label(r1, text="Record Mouse Moves", font=("Helvetica Neue", 12),
                 fg=C["text"], bg=C["card"]).pack(side="left")
        self.rec_moves_var = tk.BooleanVar(value=True)
        tk.Checkbutton(r1, variable=self.rec_moves_var, bg=C["card"],
                       activebackground=C["card"], selectcolor=C["input"],
                       fg=C["accent"]).pack(side="right")

        tk.Frame(card, bg=C["border"], height=1).pack(fill="x", pady=2)

        r2 = tk.Frame(card, bg=C["card"]); r2.pack(fill="x", pady=(10,10))
        tk.Label(r2, text="Playback Speed", font=("Helvetica Neue", 12),
                 fg=C["text"], bg=C["card"]).pack(side="left")
        self.speed_var = tk.StringVar(value="1.0")
        speed_menu = tk.OptionMenu(r2, self.speed_var, "0.25", "0.5", "1.0", "1.5", "2.0", "4.0")
        style_menu(speed_menu); speed_menu.pack(side="right")

        tk.Frame(card, bg=C["border"], height=1).pack(fill="x", pady=2)

        r3 = tk.Frame(card, bg=C["card"]); r3.pack(fill="x", pady=(10,0))
        tk.Label(r3, text="Loop Count (0 = ∞)", font=("Helvetica Neue", 12),
                 fg=C["text"], bg=C["card"]).pack(side="left")
        self.loop_var = tk.StringVar(value="1")
        tk.Entry(r3, textvariable=self.loop_var, font=("SF Mono", 14, "bold"), fg=C["text"],
                 bg=C["input"], insertbackground=C["accent"],
                 highlightbackground=C["border"], highlightcolor=C["bfocus"],
                 highlightthickness=1, relief="flat", width=4, justify="center").pack(side="right")

        # Stats card
        card = make_card(frame, "RECORDING STATS")
        sr = tk.Frame(card, bg=C["card"]); sr.pack(fill="x")

        left = tk.Frame(sr, bg=C["card"]); left.pack(side="left", expand=True, fill="x")
        tk.Label(left, text="EVENTS", font=("Helvetica Neue", 9), fg=C["dim"], bg=C["card"]).pack(anchor="w")
        self.rec_count_lbl = tk.Label(left, text="0", font=("SF Mono", 26, "bold"), fg=C["orange"], bg=C["card"])
        self.rec_count_lbl.pack(anchor="w")

        tk.Frame(sr, bg=C["border"], width=1).pack(side="left", fill="y", padx=16)

        right = tk.Frame(sr, bg=C["card"]); right.pack(side="left", expand=True, fill="x")
        tk.Label(right, text="DURATION", font=("Helvetica Neue", 9), fg=C["dim"], bg=C["card"]).pack(anchor="w")
        self.rec_dur_lbl = tk.Label(right, text="0.0s", font=("SF Mono", 26, "bold"), fg=C["purple"], bg=C["card"])
        self.rec_dur_lbl.pack(anchor="w")

        # Record / Play buttons
        bf = tk.Frame(frame, bg=C["bg"]); bf.pack(fill="x", pady=(4,0))

        btn_row = tk.Frame(bf, bg=C["bg"]); btn_row.pack(fill="x")

        self.rec_btn = make_btn(btn_row, "⏺  Record (F7)", C["red"], self.toggle_recording, 13)
        self.rec_btn.pack(side="left", expand=True, fill="x", padx=(0,4))

        self.play_btn = make_btn(btn_row, "▶  Play (F8)", C["accent"], self.toggle_playback, 13)
        self.play_btn.pack(side="left", expand=True, fill="x", padx=(4,0))

        # Save / Load
        io_row = tk.Frame(bf, bg=C["bg"]); io_row.pack(fill="x", pady=(8,0))
        make_btn(io_row, "💾 Save", C["card"], self._save_macro, 11).pack(side="left", expand=True, fill="x", padx=(0,4))
        make_btn(io_row, "📂 Load", C["card"], self._load_macro, 11).pack(side="left", expand=True, fill="x", padx=(4,0))

        # Recorder status
        sf = tk.Frame(bf, bg=C["bg"]); sf.pack(fill="x", pady=(8,0))
        self.rec_status_dot = tk.Label(sf, text="●", font=("Helvetica Neue", 10), fg=C["dim"], bg=C["bg"])
        self.rec_status_dot.pack(side="left")
        self.rec_status_lbl = tk.Label(sf, text="  Ready — press F7 to record (Esc to stop)",
                                       font=("Helvetica Neue", 11), fg=C["dim"], bg=C["bg"])
        self.rec_status_lbl.pack(side="left")

    # ── Clicker Logic ────────────────────────────────────────────────────────
    
    def _sync_interval(self):
        def si(v):
            try: return max(0, int(v.get()))
            except: return 0
        self.clicker.set_interval(si(self.interval_vars["hours"]), si(self.interval_vars["minutes"]),
                                  si(self.interval_vars["seconds"]), si(self.interval_vars["ms"]))

    def _reset_stats(self):
        self.clicker.reset(); self.session_start = None
        self.click_lbl.config(text="0"); self.session_lbl.config(text="00:00")

    def toggle_clicker(self):
        if self.clicker.running: self._stop_clicker()
        else: self._start_clicker()

    def _start_clicker(self):
        self._sync_interval(); self.clicker.start(); self.session_start = time.time()
        self.toggle_btn.config(text="■  Stop Clicking", bg=C["red"], activebackground=C["red"])
        self.status_dot.config(fg=C["green"]); self.status_lbl.config(text="  Running", fg=C["green"])

    def _stop_clicker(self):
        self.clicker.stop()
        self.toggle_btn.config(text="▶  Start Clicking", bg=C["green"], activebackground=C["green"])
        self.status_dot.config(fg=C["dim"]); self.status_lbl.config(text="  Idle — press F6", fg=C["dim"])

    # ── Recorder Logic ───────────────────────────────────────────────────────

    def toggle_recording(self):
        if self.recorder.recording: self._stop_recording()
        else: self._start_recording()

    def _start_recording(self):
        if self.recorder.playing:
            self._stop_playback()
        self.recorder.record_mouse_moves = self.rec_moves_var.get()
        self.recorder.start_recording()
        self.rec_btn.config(text="■  Stop (Esc/F7)", bg="#d62828", activebackground="#d62828")
        self.rec_status_dot.config(fg=C["red"])
        self.rec_status_lbl.config(text="  Recording... (Press Esc to stop)", fg=C["red"])
        self.rec_count_lbl.config(text="0")
        self.rec_dur_lbl.config(text="0.0s")

    def _stop_recording(self):
        self.recorder.stop_recording()

    def _sync_recording_stopped(self):
        self.rec_btn.config(text="⏺  Record (F7)", bg=C["red"], activebackground=C["red"])
        dur = f"{self.recorder.duration:.1f}s"
        self.rec_dur_lbl.config(text=dur)
        self.rec_status_dot.config(fg=C["green"])
        self.rec_status_lbl.config(text=f"  Recorded {self.recorder.event_count} events ({dur})", fg=C["green"])

    def toggle_playback(self):
        if self.recorder.playing: self._stop_playback()
        else: self._start_playback()

    def _start_playback(self):
        if self.recorder.recording:
            self._stop_recording()
        if not self.recorder.events:
            self.rec_status_lbl.config(text="  Nothing to play — record first!", fg=C["orange"])
            return
        try: self.recorder.playback_speed = float(self.speed_var.get())
        except: self.recorder.playback_speed = 1.0
        try: self.recorder.loop_count = max(0, int(self.loop_var.get()))
        except: self.recorder.loop_count = 1

        self.recorder.start_playback()
        self.play_btn.config(text="■  Stop (F8)", bg=C["red"], activebackground=C["red"])
        self.rec_status_dot.config(fg=C["accent"])
        self.rec_status_lbl.config(text="  Playing...", fg=C["accent"])

    def _stop_playback(self):
        self.recorder.stop_playback()
        self.play_btn.config(text="▶  Play (F8)", bg=C["accent"], activebackground=C["accent"])
        self.rec_status_dot.config(fg=C["dim"])
        self.rec_status_lbl.config(text="  Playback stopped", fg=C["dim"])

    def _on_playback_done(self):
        self.play_btn.config(text="▶  Play (F8)", bg=C["accent"], activebackground=C["accent"])
        self.rec_status_dot.config(fg=C["green"])
        self.rec_status_lbl.config(text="  Playback complete ✓", fg=C["green"])

    def _update_rec_count(self, n):
        self.rec_count_lbl.config(text=str(n))

    def _update_play_progress(self, i, total):
        self.rec_status_lbl.config(text=f"  Playing {i}/{total}...", fg=C["accent"])

    def _save_macro(self):
        if not self.recorder.events:
            messagebox.showwarning("No Macro", "Record a macro first!")
            return
        path = filedialog.asksaveasfilename(defaultextension=".json",
                                            filetypes=[("Macro files", "*.json")])
        if path:
            self.recorder.save(path)
            self.rec_status_lbl.config(text=f"  Saved ✓", fg=C["green"])

    def _load_macro(self):
        path = filedialog.askopenfilename(filetypes=[("Macro files", "*.json")])
        if path:
            self.recorder.load(path)
            self.rec_count_lbl.config(text=str(self.recorder.event_count))
            self.rec_dur_lbl.config(text=f"{self.recorder.duration:.1f}s")
            self.rec_status_lbl.config(text=f"  Loaded {self.recorder.event_count} events ✓", fg=C["green"])

    # ── Stats Tick ───────────────────────────────────────────────────────────

    def _tick(self):
        self.click_lbl.config(text=f"{self.clicker.click_count:,}")
        if self.session_start and self.clicker.running:
            e = int(time.time() - self.session_start)
            m, s = divmod(e, 60); h, m = divmod(m, 60)
            self.session_lbl.config(text=f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}")
        self.root.after(50, self._tick)

    # ── Global Hotkeys ───────────────────────────────────────────────────────

    def _start_hotkey_listener(self):
        def on_press(key):
            if key == Key.f6:
                self.root.after(0, self.toggle_clicker)
            elif key == Key.f7:
                self.root.after(0, self.toggle_recording)
            elif key == Key.f8:
                self.root.after(0, self.toggle_playback)
        listener = KeyboardListener(on_press=on_press)
        listener.daemon = True
        listener.start()

    def run(self):
        self.root.mainloop()

# ─── Entry Point ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = AutoClickerApp()
    app.run()
