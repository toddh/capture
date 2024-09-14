import datetime
import logging
import traceback
from time import sleep

from libcamera import Transform
from picamera2 import Picamera2
from picamera2 import Preview

# from adaptive_threshold import AdaptiveThreshold
# from histogram_difference import HistogramDifference
from image_saver import ImageSaver
from opencv_object_detection import OpenCVObjectDetection
import monitor_pir

class ImageCaptureLoop:
    """This class is the overall motion detector loop.  Currently, it only supports the OpenCV algorithm."""

    def __init__(self, config, pir_thread):
        self._config = config

        self._picam2 = Picamera2(config["capture"]["camera_name"])

        self.__set_up_camera(config["preview"]["enable"])

        # self._algorithm = HistogramDifference(config)
        # self._algorithm = AdaptiveThreshold(config)
        self._algorithm = OpenCVObjectDetection(config)

        self.__image_saver = ImageSaver()
        self._save_every_seconds = config["capture"]["save_anyways_hours"] * 3600

        self._pir_thread = pir_thread

    def start(self):
        """
        Starts the camera and runs the loop.
        """
        self._picam2.start()
        self.loop()

    def loop(self):
        # previous_image = self._picam2.capture_image("main")
        time_of_last_save = (
            datetime.datetime.now()
        )  # Not really last image, but default value so math works

        # keyboard_input.print_overrides()

        logger = logging.getLogger()
        logger.debug(f"initiating loop with config: {str(self._config)}")


        while True:
            try:
                pir = self._pir_thread.pir_detected()

                if self._config["capture"]["process_stream"] == "lores":
                    current_array = self._picam2.capture_array("lores")
                else:
                    current_array = self._picam2.capture_array("main")

                capture_time = datetime.datetime.now()

                algorithm_data = {}
                motion_detected = self._algorithm.detect_motion(
                    current_array, capture_time, pir, algorithm_data
                )

                if self._config["capture"]["print_data"]:
                    self._algorithm.print_algorithm_data(
                        algorithm_data, motion_detected
                    )

                logger.debug(f"Checked image at: {capture_time:%H:%M:%S} Motion detected: {motion_detected}")
                
                if motion_detected or pir or (
                    (capture_time - time_of_last_save).total_seconds()
                    > self._save_every_seconds
                ):
                    if self._config["capture"]["process_stream"] == "lores":
                         current_array = self._picam2.capture_array("main")

                    self.__image_saver.save_array(
                        current_array,
                        capture_time,
                        motion_detected,
                        pir,
                        self._algorithm.get_object_detection_data(algorithm_data),
                    )
                time_of_last_save = capture_time

                # previous_image = current_image

                # key = keyboard_input.pressed_key()
                # if key is not None:
                #     keyboard_input.input_override(key, self._config)

            except Exception as e:
                logging.error(f"An error occurred in the image capture loop: {e}")
                traceback.print_exc()
                continue

            sleep(self._config["capture"]["interval"])



    def __set_up_camera(self, enable_preview):
        """
        Configures the camera, preview window and encoder.

        :param enable_preview: enables preview window
        """

        # TODO: Reenable setting the size of the main stream
        
        if self._config['capture']['flip']:
            transform = Transform(vflip=True, hflip=True)
        else:
            transform = Transform()
        still_config = self._picam2.create_still_configuration(
            transform=transform,
            buffer_count=4,
            main={"format": "XBGR8888"
            },
            lores={
                "format": "XBGR8888",
                "size": (
                self._config["capture"]["lores"]["width"],
                self._config["capture"]["lores"]["height"],
                ),
            },
            display="lores",
        )

        logging.info(f"_picam2 config: {still_config}")

        self._picam2.configure(still_config)

        if enable_preview:
            self._picam2.start_preview(
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
        size = self._picam2.capture_metadata()["ScalerCrop"][2:]
        self._picam2.capture_metadata()
        size = [int(s * self.__zoom_factor) for s in size]
        offset = [(r - s) // 2 for r, s in zip(self._picam2.sensor_resolution, size)]
        self._picam2.set_controls({"ScalerCrop": offset + size})

    def cleanup(self):
        """
        Cleans up the camera and preview window.
        """
        self._picam2.stop()
        self._algorithm.cleanup()
