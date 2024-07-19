import datetime
import logging
import time
from PIL import Image, ImageFilter
from picamera2 import Picamera2, Preview
from image_saver import ImageSaver

class HistogramDifference:
    """This class contains the main logic for motion detection."""

    def __init__(self, config, picam2):
        """MotionDetector
        :param args: command line arguments
        """
        self.__min_pixel_diff = config["histogram"]["min_pixel_diff"]
        self.__save_every = config["histogram"]["save_every"]
        self.__blur = config["histogram"]["blur"]
        self.__lores_width = config["histogram"]["width"]
        self.__lores_height = config["histogram"]["height"]

        self.__max_time_since_last_detection_seconds = config["capture"]["anyways"]

        self.__time_of_last_image = None
        self.__picam2 = picam2
        self.__time_of_last_image = None

        self.__image_saver = ImageSaver()

    def loop(self):
        """
        Runs the actual motion detection loop that, optionally, triggers sends the recording via email.
        """
        previous_frame = None
        self.__time_of_last_image = datetime.datetime.now()
        detection_count = 0

        while True:
            try:
                current_frame = self.__picam2.capture_buffer("lores")
                # capture_buffer returns a 1d array.  This makes it a 2D array.  Picamera2 does have a helper make_array. Why don't we use that?
                # And we're doing lores, I assume to make the math easier.  Shouldn't we configure the camera that way?
                current_frame = current_frame[:self.__lores_width * self.__lores_height].reshape(self.__lores_height, self.__lores_width)

                if previous_frame is not None:
                    hist_diff = self.__calculate_histogram_difference(current_frame, previous_frame, self.__blur, detection_count % self.__save_every == 0)
                    if hist_diff > self.__min_pixel_diff:
                        logging.info(f"start capturing at: {datetime.datetime.now()}")
                        self.__image_saver.capture(True, hist_diff)
                        self.__time_of_last_image = datetime.datetime.now()
                    else:
                        if self.__is_max_time_since_last_motion_detection_exceeded():
                            logging.info("max time since last motion detection exceeded")
                            self.__image_saver.capture(False, hist_diff)
                            self.__time_of_last_image = datetime.datetime.now()
                previous_frame = current_frame
                detection_count += 1
            except Exception as e:
                logging.error(f"An error occurred in the motion detection loop: {e}")
                continue

    def __calculate_histogram_difference(self, current_frame, previous_frame, blur, saveit):
        if blur:
            current_image = Image.fromarray(current_frame).filter(ImageFilter.GaussianBlur(1))
            previous_image = Image.fromarray(previous_frame).filter(ImageFilter.GaussianBlur(1))
        else:
            current_image = Image.fromarray(current_frame)
            previous_image = Image.fromarray(previous_frame)

        current_hist = current_image.histogram()
        previous_hist = previous_image.histogram()

        hist_diff = sum([abs(c - p) for c, p in zip(current_hist, previous_hist)]) / len(current_hist)
        logging.info(f"hist_diff: {hist_diff}")
        if saveit:
            self.__image_saver.save_detection_image(current_image, hist_diff)

        return hist_diff

    def __is_max_time_since_last_motion_detection_exceeded(self):
        return self.__time_of_last_image is not None and \
            ((
                     datetime.datetime.now() - self.__time_of_last_image).total_seconds() > self.__max_time_since_last_detection_seconds)
    


