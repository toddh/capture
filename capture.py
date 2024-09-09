#!/usr/bin/python3
import argparse
import tomllib
import datetime
import logging
import signal
import sys
import threading
import stats_file

import tomllib
from picamera2 import Picamera2

# from pynput import keyboard
import keyboard_input
from image_capture_loop import ImageCaptureLoop
from image_saver import ImageSaver


Picamera2.set_logging(logging.ERROR)

def command_line_handler(signum, frame):
    # res = input("Ctrl-c was pressed. Do you really want to exit? y/n ")
    res = "y"
    if res == "y":
        logging.info("stopping")
        stop()

def on_press(key_code):
    try:
        keyboard_input.record_key_pressed(key_code.char)
    except AttributeError:
        pass

def load_config():
    try:
        with open("config.toml", "rb") as f:
            config = tomllib.load(f)
    except Exception as e:
        logging.critical(f"An error occurred while configuring: {e}")
        sys.exit(1)

    # Override the configuration with command line arguments

    parser = argparse.ArgumentParser(
        prog="Capture", description="Detect motion and capture images."
    )

    parser.add_argument("-p", "--preview", action="store_true")
    args = parser.parse_args()

    if args.preview:
        config["preview"]["enable"] = True

    return config

def stop():
    # stop_event.set()  # Signal the thread to stop
    # thread.join()
    sys.exit(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    config = load_config()

    image_capture_loop = ImageCaptureLoop(config)

    image_saver = ImageSaver()
    image_saver.set_config(config)

    stats_file.start_stats_thread(config)


    # Image Processing Thread

    # listener = keyboard.Listener(
    #     on_press=on_press,
    # )
    # listener.start()lores


    signal.signal(signal.SIGINT, command_line_handler)
    image_capture_loop.start()
