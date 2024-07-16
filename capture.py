#!/usr/bin/python3
import argparse
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

# python3 capture.py --preview --min-pixel-diff 30 --recording-dir /home/admin/usbshare1/images/
# python3 capture.py --min-pixel-diff 30 --recording-dir /home/admin/usbshare1/images/

# setLevel(logging.WARNING) seems to have no impact
logging.getLogger("picamera2").disabled = True
stats_file = None

def command_line_handler(signum, frame):
    res = input("Ctrl-c was pressed. Do you really want to exit? y/n ")
    if res == 'y':
        logging.info("stopping")
        stop()

def parse_command_line_arguments():
    parser = argparse.ArgumentParser(
        description='Capture images for training from Picamera2.')
    parser.add_argument('--preview', help='enables the preview window', required=False, action='store_true')
    parser.add_argument('--preview-x', type=int, default=100,
                        help='preview window location x-axis')
    parser.add_argument('--preview-y', type=int, default=200,
                        help='preview window location y-axis')
    parser.add_argument('--preview-width', type=int, default=800,
                        help='preview window width')
    parser.add_argument('--preview-height', type=int, default=600,
                        help='preview window height')
    parser.add_argument('--zoom', type=float, default=1.0,
                        help='zoom factor (0.5 is half of the resolution and therefore the zoom is x 2)',
                        required=False)
    parser.add_argument('--width', type=int, default=1280, help='camera resolution width for high resolution',
                        required=False)
    parser.add_argument('--height', type=int, default=720, help='camera resolution height for high resolution',
                        required=False)
    parser.add_argument('--lores-width', type=int, default=320, help='camera resolution width for low resolution',
                        required=False)
    parser.add_argument('--lores-height', type=int, default=240, help='camera resolution height for low resolution',
                        required=False)
    parser.add_argument('--min-pixel-diff', type=float, default=50,
                        help='minimum number of pixel changes to detect motion (determined with numpy by calculating the mean of the squared pixel difference between two frames)',
                        required=False)
    parser.add_argument('--capture-lores', help='enables capture of lores buffer', action='store_true')
    parser.add_argument('--recording-dir', default='/home/admin/usbshare1/images/', help='directory to store recordings',
                        required=False)
    parser.add_argument('--num-images', type=int, default=5,
                        help='number of images to take')
    parser.add_argument('--max-time-since-last-detection-seconds', type=int, default=3600,
                        help='max time since last motion detection in seconds')

    return parser.parse_args()

class MotionDetector:
    """This class contains the main logic for motion detection."""
    __MAX_TIME_SINCE_LAST_MOTION_DETECTION_SECONDS = 5.0

    def __init__(self, args: argparse.Namespace):
        """MotionDetector

        :param args: command line arguments
        """
        self.__picam2 = None
        self.__time_of_last_image = None

        self.__zoom_factor = args.zoom
        self.__lores_width = args.lores_width
        self.__lores_height = args.lores_height
        self.__width = args.width
        self.__height = args.height
        self.__min_pixel_diff = args.min_pixel_diff
        self.__capture_lores = args.capture_lores

        self.__recording_dir = args.recording_dir
        self.__preview_x = args.preview_x
        self.__preview_y = args.preview_y
        self.__preview_width = args.preview_width
        self.__preview_height = args.preview_height
        self.__num_images = args.num_images
        self.__max_time_since_last_detection_seconds = args.max_time_since_last_detection_seconds

        self.__set_up_camera(args.preview)

    def start(self):
        """
        Starts the camera and runs the loop.
        """
        self.__picam2.start()
        # self.__picam2.start_encoder()

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
            logging.info(f"Capturing to file {file_path}")
            time.sleep(1)
            self.__picam2.capture_file(file_path)

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
    def __init__(self, *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

def output_stats(stop_event):
    """Writes CPU temperature to the stats file every 5 seconds until stop_event is set."""
    while not stop_event.is_set():
        recording_time = datetime.datetime.now()
        cpu = CPUTemperature()
        stats_file.write(f"{recording_time:%Y-%m-%d %H:%M:%S} {cpu.temperature}\n")
        time.sleep(300)

def open_stat_file(directory):
    """Creates the directory if it doesn't exist and opens a new stats file in write mode."""
    try:
        os.makedirs(directory, exist_ok=True)
    except OSError as e:
        logging.critical(f"Error creating directory {directory}: {e}")
        return None

    recording_time = datetime.datetime.now()
    file_name = f"{directory}/stats-{recording_time:%Y-%m-%d %H%M%S}.txt"
    try:
        stats_file = open(file_name, "w")
        stats_file.write("CPU temperature\n")
        return stats_file
    except IOError as e:
        logging.critical(f"Error opening file {file_name}: {e}")
        return None

def stop():
    stop_event.set()  # Signal the thread to stop
    thread.join()
    sys.exit(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    command_line_arguments = parse_command_line_arguments()
    motion_detector = MotionDetector(command_line_arguments)

    stats_file = open_stat_file(command_line_arguments.recording_dir)
    stop_event = threading.Event()
    thread = StoppableThread(target=output_stats, args=(stop_event,))
    thread.start()

    signal.signal(signal.SIGINT, command_line_handler)
    motion_detector.start()
