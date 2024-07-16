#!/usr/bin/python3
import argparse
import tomllib
import datetime
import logging
import os
import signal
import sys
import time
from gpiozero import CPUTemperature
import threading

from PIL import Image
from picamera2 import Picamera2, Preview


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

class MotionDetector:
    """This class contains the main logic for motion detection."""

    def __init__(self, config):
        """MotionDetector
        :param args: command line arguments
        """
        self.__enable_preview = config["preview"]["enable"]
        self.__zoom_factor = config["preview"]["zoom"]
        self.__lores_width = config["lores"]["width"]
        self.__lores_height = config["lores"]["height"]
        self.__width = config["hires"]["width"]
        self.__height = config["hires"]["height"]
        self.__min_pixel_diff = config["detection"]["min_pixel_diff"]
        self.__capture_lores = config["capture"]["lores"]

        self.__recording_dir = config["capture"]["dir"]
        self.__preview_x = config["preview"]["x"]
        self.__preview_y = config["preview"]["y"]
        self.__preview_width = config["preview"]["width"]
        self.__preview_height = config["preview"]["height"]
        self.__num_images = config["capture"]["images"]
        self.__max_time_since_last_detection_seconds = config["capture"]["anyways"]

        self.__picam2 = None
        self.__time_of_last_image = None
        self.__set_up_camera(self.__enable_preview)

    def start(self):
        """
        Starts the camera and runs the loop.
        """
        self.__picam2.start()
        self.__set_zoom_factor()
        self.__loop()

    def __loop(self):
        """
        Runs the actual motion detection loop that, optionally, triggers sends the recording via email.
        """
        w, h = self.__lsize
        previous_frame = None
        self.__time_of_last_image = datetime.datetime.now()

        while True:
            try:
                current_frame = self.__picam2.capture_buffer("lores" if self.__capture_lores else "main")
                current_frame = current_frame[:w * h].reshape(h, w)
                if previous_frame is not None:
                    hist_diff = self.__calculate_histogram_difference(current_frame, previous_frame)
                    if hist_diff > self.__min_pixel_diff:
                        logging.info(f"start capturing at: {datetime.datetime.now()}")
                        self.__capture(self.__num_images, True, hist_diff)
                        self.__time_of_last_image = datetime.datetime.now()
                    else:
                        if self.__is_max_time_since_last_motion_detection_exceeded():
                            logging.info("max time since last motion detection exceeded")
                            self.__capture(1, False, hist_diff)
                            self.__time_of_last_image = datetime.datetime.now()
                previous_frame = current_frame
            except Exception as e:
                logging.error(f"An error occurred in the motion detection loop: {e}")
                continue

    def __calculate_histogram_difference(self, current_frame, previous_frame):
        current_image = Image.fromarray(current_frame)
        previous_image = Image.fromarray(previous_frame)

        current_hist = current_image.histogram()
        previous_hist = previous_image.histogram()

        hist_diff = sum([abs(c - p) for c, p in zip(current_hist, previous_hist)]) / len(current_hist)
        # logging.info(f"Diff = {hist_diff}")

        return hist_diff

    def __is_max_time_since_last_motion_detection_exceeded(self):
        return self.__time_of_last_image is not None and \
            ((
                     datetime.datetime.now() - self.__time_of_last_image).total_seconds() > self.__max_time_since_last_detection_seconds)

    def __capture(self, num_images, triggered, diff):
        for _ in range(num_images):
            file_path = self.__get_capture_file_name(triggered, diff)
            # logging.info(f"Capturing to file {file_path}")
            try:
                self.__picam2.capture_file(file_path)
            except Exception as e:
                logging.error(f"An error occurred capturing to the file: {e}")

            time.sleep(1)


    def __get_capture_file_name(self, triggered, diff):
        recording_time = datetime.datetime.now()
        if (triggered):
            file_name = f"{self.__recording_dir}{recording_time:%Y-%m-%d %H%M%S}.{recording_time.microsecond // 1000:03d}-{diff:04.0f}-t.jpg"
        else:
            file_name = f"{self.__recording_dir}{recording_time:%Y-%m-%d %H%M%S}.{recording_time.microsecond // 1000:03d}-{diff:04.0f}.jpg"
        return file_name

    def __set_up_camera(self, enable_preview):
        """
        Configures the camera, preview window and encoder.

        :param enable_preview: enables preview window
        """
        self.__lsize = (self.__lores_width, self.__lores_height)
        self.__picam2 = Picamera2()
        video_config = self.__picam2.create_video_configuration(
            main={"size": (self.__width, self.__height), "format": "YUV420"},
            lores={"size": self.__lsize, "format": "YUV420"})
        still_config = self.__picam2.create_still_configuration()
        self.__picam2.configure(still_config)

        if enable_preview:
            self.__picam2.start_preview(Preview.QTGL, x=self.__preview_x, y=self.__preview_y,
                                        width=self.__preview_width, height=self.__preview_height)

    def __set_zoom_factor(self):
        """
        Sets the zoom factor of the camera.
        """
        size = self.__picam2.capture_metadata()['ScalerCrop'][2:]
        self.__picam2.capture_metadata()
        size = [int(s * self.__zoom_factor) for s in size]
        offset = [(r - s) // 2 for r, s in zip(self.__picam2.sensor_resolution, size)]
        self.__picam2.set_controls({"ScalerCrop": offset + size})


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

    recording_time = datetime.datetime.now()
    stats_file_name = f"{config['capture']['dir']}/stats-{recording_time:%Y-%m-%d %H%M%S}.txt"
    # stats_file = open_stat_file(config["capture"]["dir"])
    # stop_event = threading.Event()
    # thread = StoppableThread(target=output_stats, args=(stop_event, config["capture"]["dir"]))
    thread = threading.Thread(target=output_stats, args=(stats_file_name,config['stats']['interval']))
    thread.daemon = True
    thread.start()

    signal.signal(signal.SIGINT, command_line_handler)
    motion_detector.start()
