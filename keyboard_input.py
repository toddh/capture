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

def print_overrides():
    print(" ")
    print("Keyboard Overrides:")
    print("d: Change min_hist_diff")
    print("r: Change blur radius")
    print(" ")


def input_override(key, config):
    if key == 'd':
        print (" ")
        str = input("Enter new min_hist_diff: ")
        str = str[1:]           # Hacky way to ignore the first character
        try:
            config["histogram"]["min_hist_diff"] = int(str)
        except ValueError:
            pass
        record_key_pressed(None)
    elif key == 'r':
        print (" ")
        str = input("Enter new blur radius: ")
        str = str[1:]           # Hacky way to ignore the first character
        try:
            config["histogram"]["radius"] = int(str)
        except ValueError:
            pass
        record_key_pressed(None)
