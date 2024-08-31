import datetime
import logging
import time
from PIL import Image, ImageFilter
from picamera2 import Picamera2, Preview
from libcamera import Transform

fomr image_saver import ImageSaver
from histogram_difference import HistogramDifference

class ImageCaptureLoop:
    """This class is the overall motion detector loop.  It can use a variety of different algorithms."""

    def __init__(self, config):
        self.__save_every = config["histogram"]["save_every"]

        self.__enable_preview = config["preview"]["enable"]
        self.__zoom_factor = config["preview"]["zoom"]
        self.__blur = config["histogram"]["blur"]

        self.__lores_width = config["histogram"]["width"]
        self.__lores_height = config["histogram"]["height"]

        self.__enable_preview = config["preview"]["enable"]
        self.__preview_x = config["preview"]["x"]
        self.__preview_y = config["preview"]["y"]
        self.__preview_width = config["preview"]["width"]
        self.__preview_height = config["preview"]["height"]

        self.picam2 = Picamera2()

        self.__max_time_since_last_detection_seconds = config["capture"]["anyways"]

        self.__time_of_last_image = None
        self.__set_up_camera(self.__enable_preview)

        self.__algorithm = HistogramDifference(config, self.picam2)
        self.__image_saver = ImageSaver()

    def start(self):
        """
        Starts the camera and runs the loop.
        """
        self.picam2.start()
        # self.__set_zoom_factor()
        self.loop()


    def loop(self):
        previous_frame = None
        image_count = 0

        while True:
            try:
                current_frame = self.__picam2.capture_buffer("lores")
                recording_time = datetime.datetime.now()

                # TODO: capture_buffer returns a 1d array.  This makes it a 2D array.  Picamera2 does have a helper make_array. Why don't we use that?
                # TODO: And we're doing lores, I assume to make the math easier.  Shouldn't we configure the camera that way?
                # TODO: Should we do the main rather than lores?
                current_frame = current_frame[:self.__lores_width * self.__lores_height].reshape(self.__lores_height, self.__lores_width)

                if previous_frame is not None:
                
                    meta_data = {}
                    motion_detected = self.__algorithm.__detect_motion(current_frame, previous_frame, meta_data)

                    if motion_detected or (image_count % self.__save_every == 0):  # TODO: Determine whether we'd rather 
                        self.__image_saver.save_detection_image(Image.fromarray(current_frame), recording_time, motion_detected, meta_data)
                        # TODO: Figure out how to display live information for debugging

                previous_frame = current_frame
                image_count += 1  # TODO: Figure out what happens if we overrun this? Change to a reset?
            except Exception as e:
                logging.error(f"An error occurred in the motion detection loop: {e}")
                continue


    def __set_up_camera(self, enable_preview):
        """
        Configures the camera, preview window and encoder.

        :param enable_preview: enables preview window
        """
        still_config = self.picam2.create_still_configuration(
            transform=Transform(vflip=True),
            buffer_count=4,  # Mimicking preview configuration. Maybe not needed if not previewing?
            main={'format': 'XBGR8888'},
            lores={'format': 'YUV420', 'size': (self.__lores_width, self.__lores_height)},
            display="lores"
            )
        
        logging.info(f"Picam2 config: {still_config}")

        self.picam2.configure(still_config)

        if enable_preview:
            self.picam2.start_preview(Preview.QTGL, x=self.__preview_x, y=self.__preview_y, width=self.__preview_width, height=self.__preview_height)

    def __set_zoom_factor(self):
        """
        Sets the zoom factor of the camera.
        """
        size = self.picam2.capture_metadata()['ScalerCrop'][2:]
        self.picam2.capture_metadata()
        size = [int(s * self.__zoom_factor) for s in size]
        offset = [(r - s) // 2 for r, s in zip(self.picam2.sensor_resolution, size)]
        self.picam2.set_controls({"ScalerCrop": offset + size})
   
