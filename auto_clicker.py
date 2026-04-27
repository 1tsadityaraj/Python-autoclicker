import time
import sys
import pickle
from pynput import mouse, keyboard

e = []
t = None

m = mouse.Controller()
k = keyboard.Controller()

def gt():
    global t
    if t is None:
        t = time.time()
    return time.time() - t

def move(x, y):
    e.append(('mouse move', gt(), (x, y)))

def click(x, y, button, pressed):
    e.append(('mouse click', gt(), (x, y, button, pressed)))

def scro(x, y, dx, dy):
    e.append(('mouse scroll', gt(), (x, y, dx, dy)))

def press(key):
    if key == keyboard.Key.esc:
        print("\n[Esc pressed. Stopped recording.]")
        return False 
    e.append(('key_press', gt(), key))

def on_release(key):
    if key != keyboard.Key.esc:
        e.append(('key_release', gt(), key))

def play_macro():
    if not e:
        print("Nothing recorded!")
        return

    print(f"\n[Playing back {len(e)} events...]")
    start_time = time.time()
    
    for event in e:
        event_type, target_time, data = event
        
        # Wait until it's time for this event
        current_elapsed = time.time() - start_time
        if target_time > current_elapsed:
            time.sleep(target_time - current_elapsed)
            
        if event_type == 'mouse move':
            m.position = data
        elif event_type == 'mouse click':
            x, y, button, pressed = data
            m.position = (x, y)
            if pressed:
                m.press(button)
            else:
                m.release(button)
        elif event_type == 'mouse scroll':
            x, y, dx, dy = data
            m.position = (x, y)
            m.scroll(dx, dy)
        elif event_type == 'key_press':
            try:
                k.press(data)
            except Exception:
                pass
        elif event_type == 'key_release':
            try:
                k.release(data)
            except Exception:
                pass
                
    print("[Playback finished!]")

def record_macro():
    print("=======================================")
    print("  Recording Macro...")
    print("=======================================")
    print("Move your mouse and type. Press [ESC] to stop recording.\n")
    
    with mouse.Listener(on_move=move, on_click=click, on_scroll=scro) as ml:
        with keyboard.Listener(on_press=press, on_release=on_release) as kl:
            kl.join()
            ml.stop()
            
    print(f"Recorded {len(e)} events.")
    with open('macro.pkl', 'wb') as f:
        pickle.dump(e, f)
    print("Saved to macro.pkl!")

def load_and_play():
    global e
    try:
        with open('macro.pkl', 'rb') as f:
            e = pickle.load(f)
    except FileNotFoundError:
        print("No macro found! Run 'python3 auto_clicker.py record' first.")
        return
        
    print("\nStarting playback in 3 seconds...")
    time.sleep(3)
    play_macro()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 auto_clicker.py [record|play]")
        sys.exit(1)
        
    command = sys.argv[1].lower()
    
    if command == "record":
        record_macro()
    elif command == "play":
        load_and_play()
    else:
        print(f"Unknown command: {command}")
        print("Available commands: record, play")
