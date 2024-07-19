import datetime
import logging
import time
from PIL import Image, ImageFilter
from picamera2 import Picamera2, Preview

from histogram_difference import HistogramDifference

class MotionDetector:
    """This class is the overall motion detector loop.  It can use a variety of different algorithms."""

    def __init__(self, config):
        self.__enable_preview = config["preview"]["enable"]
        self.__zoom_factor = config["preview"]["zoom"]

        self.__lores_width = config["histogram"]["width"]
        self.__lores_height = config["histogram"]["height"]

        self.__preview_x = config["preview"]["x"]
        self.__preview_y = config["preview"]["y"]
        self.__preview_width = config["preview"]["width"]
        self.__preview_height = config["preview"]["height"]

        self.picam2 = Picamera2()

        self.__set_up_camera(self.__enable_preview)

        self.__algorithm = HistogramDifference(config, self.picam2)

    def start(self):
        """
        Starts the camera and runs the loop.
        """
        self.picam2.start()
        # self.__set_zoom_factor()
        self.__algorithm.loop()


    def __set_up_camera(self, enable_preview):
        """
        Configures the camera, preview window and encoder.

        :param enable_preview: enables preview window
        """
        still_config = self.picam2.create_still_configuration(lores={"size": (self.__lores_width, self.__lores_height)})
        self.picam2.configure(still_config)

        if enable_preview:
            self.picam2.start_preview(Preview.QTGL, x=self.__preview_x, y=self.__preview_y,
                                        width=self.__preview_width, height=self.__preview_height)

    def __set_zoom_factor(self):
        """
        Sets the zoom factor of the camera.
        """
        size = self.picam2.capture_metadata()['ScalerCrop'][2:]
        self.picam2.capture_metadata()
        size = [int(s * self.__zoom_factor) for s in size]
        offset = [(r - s) // 2 for r, s in zip(self.picam2.sensor_resolution, size)]
        self.picam2.set_controls({"ScalerCrop": offset + size})
   
