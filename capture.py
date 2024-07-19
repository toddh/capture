#!/usr/bin/python3
import tomllib
import datetime
import logging
import os
import signal
import sys
import time
from gpiozero import CPUTemperature
import threading

from PIL import Image, ImageFilter
from picamera2 import Picamera2, Preview

from motion_detector import MotionDetector
from image_saver import ImageSaver

# setLevel(logging.WARNING) seems to have no impact
Picamera2.set_logging(logging.ERROR)

def command_line_handler(signum, frame):
    res = input("Ctrl-c was pressed. Do you really want to exit? y/n ")
    if res == 'y':
        logging.info("stopping")
        stop()

def load_config():
    try:
        with open("config.toml", "rb") as f:
            config = tomllib.load(f)
    except Exception as e:
        logging.critical(f"An error occurred while configuring: {e}")
        sys.exit(1)

    return config


class StoppableThread(threading.Thread):
    """Class to create a thread that can be stopped."""
    def __init__(self, *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

def output_stats(stats_file_name, interval):
    """Writes CPU temperature to the stats file every hour until stop_event is set."""

    while True:
        stats_file = open_stat_file(stats_file_name)
        recording_time = datetime.datetime.now()
        cpu = CPUTemperature()
        stats_file.write(f"{recording_time:%Y-%m-%d %H:%M:%S} {cpu.temperature}\n")
        stats_file.close()
        time.sleep(interval)

def open_stat_file(stats_file_name):
    try:
        stats_file = open(stats_file_name, "a+")
        stats_file.write("CPU temperature\n")
        return stats_file
    except IOError as e:
        logging.error(f"Error opening file {file_name}: {e}")
        return None

def stop():
    # stop_event.set()  # Signal the thread to stop
    # thread.join()
    sys.exit(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    config = load_config()

    motion_detector = MotionDetector(config)

    image_saver = ImageSaver()
    image_saver.set_defaults(config["capture"]["output_dir"], config["capture"]["num_images"], motion_detector.picam2)


    recording_time = datetime.datetime.now()
    stats_file_name = f"{config['capture']['output_dir']}/stats-{recording_time:%Y-%m-%d %H%M%S}.txt"
    # stats_file = open_stat_file(config["capture"]["dir"])
    # stop_event = threading.Event()
    # thread = StoppableThread(target=output_stats, args=(stop_event, config["capture"]["dir"]))
    thread = threading.Thread(target=output_stats, args=(stats_file_name,config['stats']['interval']))
    thread.daemon = True
    thread.start()

    signal.signal(signal.SIGINT, command_line_handler)
    motion_detector.start()
