import datetime
import logging
import sys
from time import sleep

from libcamera import Transform
from picamera2 import Picamera2
from picamera2 import Preview
from PIL import Image

from histogram_difference import HistogramDifference
from image_saver import ImageSaver


class ImageCaptureLoop:
    """This class is the overall motion detector loop.  It can use a variety of different algorithms."""

    def __init__(self, config):
        self._config = config

        self.picam2 = Picamera2()

        self.__set_up_camera(config["preview"]["enable"])

        self.__algorithm = HistogramDifference(config)
        self.__image_saver = ImageSaver()
        self._save_every_seconds = config["capture"]["save_anyways_hours"] * 3600

    def start(self):
        """
        Starts the camera and runs the loop.
        """
        self.picam2.start()
        self.loop()

    def loop(self):
        previous_frame = None
        time_of_last_image = (
            datetime.datetime.now()
        )  # Not really last image, but default value so math works

        while True:
            try:
                current_frame = self.picam2.capture_buffer("lores")
                capture_time = datetime.datetime.now()

                # TODO: capture_buffer returns a 1d array.  This makes it a 2D array.  Picamera2 does have a helper make_array. Why don't we use that?
                # TODO: And we're doing lores, I assume to make the math easier.  Shouldn't we configure the camera that way?
                # TODO: Should we do the main rather than lores?

                # The capture_buffer method will give you the raw camera data for each frame (a JPEG bitstream from an MJPEG camera,
                # or an uncompressed YUYV image from a YUYV camera).

                # (buffer,), metadata = self.picam2.capture_buffers(["lores"])
                # img = self.picam2.helpers.make_image(
                #     buffer, self.picam2.camera_configuration()["lores"]
                # )
                # self.picam2.helpers.save(img, metadata, "file.jpg")

                current_frame = current_frame[
                    : self._config["histogram"]["width"]
                    * self._config["histogram"]["height"]
                ].reshape(
                    self._config["histogram"]["height"],
                    self._config["histogram"]["width"],
                )

                if previous_frame is not None:
                    algorithm_data = {}
                    motion_detected = self.__algorithm.detect_motion(
                        current_frame, previous_frame, algorithm_data
                    )

                    self.__algorithm.print_algorithm_data(
                        algorithm_data, motion_detected
                    )

                    if motion_detected or (
                        (capture_time - time_of_last_image).total_seconds()
                        > self._save_every_seconds
                    ):
                        self.__image_saver.save_image(
                            Image.fromarray(current_frame),
                            capture_time,
                            motion_detected,
                            algorithm_data,
                        )

                previous_frame = current_frame
                time_of_last_image = capture_time

            except Exception as e:
                logging.error(f"An error occurred in the image capture loop: {e}")
                continue

            sleep(self._config["capture"]["interval"])

    def __set_up_camera(self, enable_preview):
        """
        Configures the camera, preview window and encoder.

        :param enable_preview: enables preview window
        """
        still_config = self.picam2.create_still_configuration(
            transform=Transform(vflip=True),
            buffer_count=4,  # Mimicking preview configuration. Maybe not needed if not previewing?
            main={"format": "XBGR8888"},
            lores={
                "format": "YUV420",
                "size": (
                    self._config["histogram"]["width"],
                    self._config["histogram"]["height"],
                ),
            },
            display="lores",
        )

        logging.info(f"Picam2 config: {still_config}")

        self.picam2.configure(still_config)

        if enable_preview:
            self.picam2.start_preview(
                Preview.QTGL,
                x=self._config["preview"]["x"],
                y=self._config["preview"]["y"],
                width=self._config["preview"]["width"],
                height=self._config["preview"]["height"],
            )

    def __set_zoom_factor(self):
        """
        Sets the zoom factor of the camera.
        """
        size = self.picam2.capture_metadata()["ScalerCrop"][2:]
        self.picam2.capture_metadata()
        size = [int(s * self.__zoom_factor) for s in size]
        offset = [(r - s) // 2 for r, s in zip(self.picam2.sensor_resolution, size)]
        self.picam2.set_controls({"ScalerCrop": offset + size})
