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
# from opencv_object_detection import OpenCVObjectDetection
from tensor_flow_detect import TensorFlowDetect


class ImageCaptureLoop:
    """This class is the overall motion detector loop.

       Supported opencv_object_detection. Adding tensor_flow_detect.
    """

    def __init__(self, config, pir_thread):
        self._config = config

        self._camera_list = self.__set_up_cameras(
            config["capture"]["cameras"], config["preview"]["enable"]
        )

        # self._algorithm = HistogramDifference(config)
        # self._algorithm = AdaptiveThreshold(config)
        # self._algorithm = OpenCVObjectDetection(config)
        self._algorithm = TensorFlowDetect(config)

        self._image_saver = ImageSaver()
        self._save_every_seconds = config["capture"]["save_anyways_hours"] * 3600

        self._pir_thread = pir_thread

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

        # keyboard_input.print_overrides()

        logger = logging.getLogger()
        logger.debug(f"initiating loop with config: {str(self._config)}")

        while True:
            try:
                pir = self._pir_thread.pir_detected()

                # GET THE IMAGE
                # TensorFlow uses capture_buffer.  OpenCV uses capture_array.
                # "The capture_buffer method will give you the raw camera data for each frame (a JPEG"
                # bitstream from an MJPEG camera, or an uncompressed YUYV image from a YUYV camera)"
                # "capture_array() returns a numpy array representing the image"
                # Both of these have a plural version.

                grey = self._algorithm.get_image(self._camera_list[0])  # TODO: Either allow more than one in the code, or remove it as a config option
                
                # FORMER OPENCV CODE:
                # capture_arrays = []
                # for picam in self._camera_list:
                #     lores_array = picam.capture_array("lores")
                #     main_array = picam.capture_array("main")
                #     capture_arrays.append(
                #         [lores_array, main_array]
                #     )  # capture_arrays is an array where each element is also an array. The first item in the element is the lores array. The second is the main.


                capture_time = datetime.datetime.now()

                algorithm_data = {}
                algorithm_data["pir"] = "True" if pir else "False"

                any_motion_detected = False

                # RUN INFERENCE AND PERFORM OBJECT DETECTION
                num_detections = self._algorithm.InferenceTensorFlow(grey)
                datum = {}
                datum["camera_name"] = 0
                datum["num_detections"] = num_detections
                algorithm_data[str(i)] = datum
                if num_detections > 0:
                    any_motion_detected = True
                # FORMER OPENCV CODE:
                # for i in range(len(capture_arrays)):
                #     datum = {}
                #     datum["camera_name"] = i
                #     any_motion_detected = self._algorithm.detect_motion(
                #         capture_arrays[i][0], capture_time, datum
                #     )  # Design decision - always run the algorithm on the lores array.
                #     algorithm_data[str(i)] = datum

                if self._config["capture"]["print_data"]:
                    self._algorithm.print_algorithm_data(
                        algorithm_data, any_motion_detected
                    )

                logger.debug(
                    f"Checked images at: {capture_time:%H:%M:%S} Motion detected: {any_motion_detected}"
                )

                if (
                    any_motion_detected
                    or pir
                    or (
                        (capture_time - time_of_last_save).total_seconds()
                        > self._save_every_seconds
                    )
                ):
                    # SAVE THE IMAGE
                     self._image_saver.save_array(
                        self._camera_list[0].capture_array("lores"),
                        self._camera_list[0].capture_array("main"),
                        capture_time,
                        any_motion_detected,
                        pir,
                        0,
                        self._algorithm.get_object_detection_data(algorithm_data),
                     )

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

                    time_of_last_save = capture_time

                # key = keyboard_input.pressed_key()
                # if key is not None:
                #     keyboard_input.input_override(key, self._config)
                # print(f"{i}: Class: {class_id} score: {detection_scores[0, i]} box: ({str(rectangle)})")

            except Exception as e:
                    logging.error(f"An error occurred in the image capture loop: {e}")
                    traceback.print_exc()
                    continue

            sleep(self._config["capture"]["interval"])

    def __set_up_cameras(self, cameras, enable_preview):
        """
        Configures the camera, preview window and encoder.

        :param cameras: a list of camera numbers to start.
        :param enable_preview: enables preview window
        """

        camera_list = []

        for camera_num in cameras:

            picam = self._algorithm.start_camera(camera_num)

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

            camera_list.append(picam)

        return camera_list

    # def __set_zoom_factor(self):
    #     """
    #     Sets the zoom factor of the camera.
    #     """
    #     size = self._picam2.capture_metadata()["ScalerCrop"][2:]
    #     self._picam2.capture_metadata()
    #     size = [int(s * self.__zoom_factor) for s in size]
    #     offset = [(r - s) // 2 for r, s in zip(self._picam2.sensor_resolution, size)]
    #     self._picam2.set_controls({"ScalerCrop": offset + size})

    # TODO: Call this when appropriate. Figure out how we're handling the camera array.
    def cleanup(self):
        """
        Cleans up the camera and preview window.
        """
        self._picam2.stop()
        self._algorithm.cleanup()
