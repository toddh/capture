import datetime
import logging
import traceback
from time import sleep
import platform

from libcamera import Transform
from picamera2 import Picamera2
from picamera2 import Preview

import numpy as np

# from adaptive_threshold import AdaptiveThreshold
# from histogram_difference import HistogramDifference
from image_saver import ImageSaver
# from opencv_object_detection import OpenCVObjectDetection
from tensor_flow_detect import TensorFlowDetect

from capture_data import CaptureData

class ImageCaptureLoop:
    """This class is the overall motion detector loop.

       Supported opencv_object_detection. Adding tensor_flow_detect.
    """

    def __init__(self, config, pir_thread = None):

        # self._algorithm = HistogramDifference(config)
        # self._algorithm = AdaptiveThreshold(config)
        # self._algorithm = OpenCVObjectDetection(config)
        self._algorithm = TensorFlowDetect(config['tflite'], config['capture']['flip'], config['preview']['enable'])

        self._camera_list = self.__set_up_cameras(
            config['capture']['cameras'], config['preview']['enable']
        )

        self._image_saver = ImageSaver()
        self._save_every_seconds = config['capture']['save_anyways_hours'] * 3600

        self._pir_thread = pir_thread
        self._delay = config['capture']['delay']

    def start(self):
        """
        Starts the cameras and run the loop.
        """

        for camera in self._camera_list:
            camera.start()

        self.loop()

    def loop(self):
        """
        Repeated loop. Each iteration capture images from all cameras and then processes it.

        The loop also checks the PIR to determine if images should be captured.
        """
        time_of_last_save = datetime.datetime(datetime.MINYEAR, 1, 1, tzinfo=None)

        logger = logging.getLogger()

        burst = False
        burst_cnt = 0

        while True:
            try:
                if self._pir_thread is not None:
                    pir = self._pir_thread.pir_detected()
                else:
                    pir = False

                # GET THE IMAGE
                # TensorFlow uses capture_buffer.  OpenCV uses capture_array.
                # "The capture_buffer method will give you the raw camera data for each frame (a JPEG"
                # bitstream from an MJPEG camera, or an uncompressed YUYV image from a YUYV camera)"
                # "capture_array() returns a numpy array representing the image"
                # Both of these have a plural version.

                grey = self._algorithm.get_image_from_camera(self._camera_list[0])  # TODO: Either allow more than one in the code, or remove it as a config option
                
                # FORMER OPENCV CODE:
                # capture_arrays = []
                # for picam in self._camera_list:
                #     lores_array = picam.capture_array("lores")
                #     main_array = picam.capture_array("main")
                #     capture_arrays.append(
                #         [lores_array, main_array]
                #     )  # capture_arrays is an array where each element is also an array. The first item in the element is the lores array. The second is the main.


                capture_data = CaptureData()
                capture_data.capture_time = datetime.datetime.now()
                capture_data.pir_fired = pir
                capture_data.node_name = platform.node()
                capture_data.camera_num = 0  # TODO: Fix this
                capture_data.object_detected = False

                # RUN INFERENCE AND PERFORM OBJECT DETECTION
                rectangles, scores, classes = self._algorithm.detect_objects(grey)

                capture_data.rectangles = rectangles
                capture_data.classes = classes
                capture_data.scores = scores   


                if len(rectangles) > 0:
                    capture_data.object_detected = True

                logger.debug(
                    f"Checked images at: {capture_data.capture_time_str()} Object detected: {capture_data.object_detected}"
                )

                if (
                    capture_data.object_detected
                    or pir
                    or (
                        (capture_data.capture_time - time_of_last_save).total_seconds()
                        > self._save_every_seconds
                    )
                    or burst
                ):
                    # SAVE THE IMAGE
                    self._image_saver.save_array(
                    self._camera_list[0].capture_array("lores"),
                    self._camera_list[0].capture_array("main"),
                    capture_data)

                    # FORMER OPENCV_CODE
                    # for i in range(len(capture_arrays)):
                    #     self._image_saver.save_array(
                    #         capture_arrays[i][0],
                    #         capture_arrays[i][1],
                    #         capture_time,
                    #         any_motion_detected,
                    #         pir,
                    #         i,
                    #         self._algorithm.get_object_detection_data(algorithm_data),
                    #     )

                    time_of_last_save = capture_data.capture_time

                    if not burst:
                        burst = True
                        burst_cnt = 3
                    else:
                        burst_cnt -= 1
                        if burst_cnt == 0:
                            burst = False

                logger.debug(f"Burst: {burst} Burst count: {burst_cnt}")

            except Exception as e:
                    logging.error(f"An error occurred in the image capture loop: {e}")
                    traceback.print_exc()
                    continue

            if not burst:
                sleep(self._delay)

    def __set_up_cameras(self, cameras, enable_preview):
        """
        Configures the camera, preview window and encoder.

        :param cameras: a list of camera numbers to start.
        :param enable_preview: enables preview window
        """

        camera_list = []

        for camera_num in cameras:

            picam = self._algorithm.start_camera(camera_num)

            camera_list.append(picam)

        return camera_list

        # THIS CODE IS WHAT WORKED WITH OPENCV.  FOR TENSORFLOW, I'M LETTING THE DETECT CLASS
        # HANDLE THE CAMERA. NEED TO THINK ABOUT HOW BEST TO ARCHITECT THIS.
        # picam = Picamera2(camera_num)

        # if self._config["capture"]["flip"]:
        #     transform = Transform(vflip=True, hflip=True)
        # else:
        #     transform = Transform()
        # still_config = picam.create_still_configuration(
        #     transform=transform,
        #     buffer_count=4,
        #     main={"format": "XBGR8888"},
        #     lores={
        #         "format": "XBGR8888",
        #         "size": (
        #             self._config["capture"]["lores"]["width"],
        #             self._config["capture"]["lores"]["height"],
        #         ),
        #     },
        #     display="lores",
        # )

        # logging.info(f"picam2 number {camera_num} config: {still_config}")

        # picam.configure(still_config)

        # if enable_preview:
        #     picam.start_preview(
        #         Preview.QTGL,
        #         x=self._config["preview"]["x"],
        #         y=self._config["preview"]["y"],
        #         width=self._config["preview"]["width"],
        #         height=self._config["preview"]["height"],
        #     )


    # TODO: Call this when appropriate. Figure out how we're handling the camera array.
    def cleanup(self):
        """
        Cleans up the camera and preview window.
        """
        self._picam2.stop()
        self._algorithm.cleanup()
