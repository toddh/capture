import threading


# Shared variable and lock
key_pressed = None
lock = threading.Lock()

def record_key_pressed(key):
    global key_pressed
    with lock:
        # Modify the shared variable
        key_pressed = key

def pressed_key():
    global key_pressed
    with lock:
        # Read the shared variable
        return key_pressed
