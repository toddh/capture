import logging
import sys

import cv2
import numpy as np
import tflite_runtime.interpreter as tflite
from picamera2 import MappedArray, Picamera2, Preview

rectangles = []
preview_width = 640
preview_height = 480

def draw_rectangles(request):
    # NOTE: THIS IS NOT PART OF OUR CLASS!
    #
    # The MappedArray needs to be given a request and the name of the stream for which we
    # want access to its image buffer. It then maps that memory into user space and presents it
    # to us as a regular numpy array, just as if we had obtained it via capture_array. Once we
    # leave the with block, the memory is unmapped and everything is cleaned up.


    for rect in rectangles:
        with MappedArray(request, "main") as m:
            for rect in rectangles:
                xmin = rect[0] * preview_width
                ymin = rect[1] * preview_height
                xmax = rect[2] * preview_width
                ymax = rect[3] * preview_height
                print(rect)
                rect_start = (int(xmin * 2) - 5, int(ymin * 2) - 5)
                rect_end = (int(xmax * 2) + 5, int(ymax * 2) + 5)
                cv2.rectangle(m.array, rect_start, rect_end, (0, 255, 0, 0))
                if len(rect) == 5:
                    text = rect[4]
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    cv2.putText(
                        m.array,
                        text,
                        (int(rect[0] * 2) + 10, int(rect[1] * 2) + 10),
                        font,
                        1,
                        (255, 255, 255),
                        2,
                        cv2.LINE_AA,
                    )


# Using the TensorFlow Lite example from Picamera2 as an example.
# examples/tensorflow/real_time_with_labels.py
#
#
# Install necessary dependences before starting,
#
# $ sudo apt update
# $ sudo apt install build-essential
# $ sudo apt install libatlas-base-dev
# $ sudo apt install python3-pip
# $ pip3 install tflite-runtime
# $ pip3 install opencv-python==4.4.0.46
# $ pip3 install pillow
# $ pip3 install numpy


class TensorFlowDetect:
    """
    TODO: Refactor as much as possible to AbstractObjectDetector
    TODO: Get it working with EfficientDet from Kagglehub:  https://www.kaggle.com/models/tensorflow/efficientdet/tfLite

    Args:
        abstract_model (_type_): _description_
    """

    def __init__(self, lores_width, lores_height, main_width, main_height, preview):
        global rectangles
        global preview_width
        global preview_height

        self._labels = self._read_label_file("coco_labels.txt")
        self._model_file_path = "mobilenet_v2.tflite"

        self._main_width = main_width
        self._main_height = main_height
        self._lores_width = lores_width
        self._lores_height = lores_height
        self._preview = preview

        self._model = "mobilenet_v2.tflite"

        rectangles = []
        preview_width = main_width
        preview_height = main_height

    def _read_label_file(self, file_path):
        with open(file_path, "r") as f:
            lines = f.readlines()
        ret = {}
        for line in lines:
            pair = line.strip().split(maxsplit=1)
            ret[int(pair[0])] = pair[1].strip()
        return ret

    def start_camera(self, camera_num):
        """
        Start Picamera2 if using that.  This is optional if we're going to obtain the image
        another way.

        Args:
            camera_num (_type_): _description_

        Returns:
            _type_: _description_
        """
        picam2 = Picamera2(camera_num)
        if self._preview:
            picam2.start_preview(Preview.QTGL)
        config = picam2.create_preview_configuration(
            main={"size": (self._main_width, self._main_height)},
            lores={"size": (self._lores_width, self._lores_height), "format": "YUV420"},
            display="main",
        )

        picam2.configure(config)

        self._stride = picam2.stream_configuration("lores")["stride"]
        # Stride = The length of each row of the image in bytes

        # TODO: Think about adding the following line in. It can be used to draw_rectangles in the preview.
        if self._preview:
            picam2.post_callback = draw_rectangles

        picam2.start()

        return picam2

    def get_image_from_camera(self, picam2):
        """
        Get the image from the camera if we started it in start_camera. The other way is to get an
        image from a file.

        Args:
            picam2 (_type_): _description_

        Returns:
            _type_: _description_
        """

        # So this is the original code to get the Y value. But it ended up getting too much.
        # So I went with the stuff down below.
        #
        # buffer = picam2.capture_buffer("lores")
        # grey = buffer[:self._stride * self._lowresHeight].reshape(self._lowresHeight, self._stride)
        # Height, width

        buffer = picam2.capture_buffer("lores")
        grey = buffer[: self._stride * self._lores_height].reshape(self._lores_height, self._stride)

        # YUv420 is a slightly special case because the first height rows give the Y channel, the
        # next height/4 rows contain the U channel and the final height/4 rows contain the V
        # channel.

        return grey

    def get_image_from_file(self, image_path):
        """
        Get the image from a file. Convert it to the proper format.

        Args:
            image_path (string): Path to image to read
        """

        img = cv2.imread(image_path)
        # img_height, img_width, _ = img.shape

        grey = cv2.cvtColor(
            img, cv2.COLOR_BGR2GRAY
        )
        grey = cv2.resize(grey, (self._lores_width, self._lores_height))

        main = cv2.cvtColor(
            img, cv2.COLOR_BGR2RGB
        )
        main = cv2.resize(img, (self._main_width, self._main_height))

        # input_data = np.clip(input_data, 0, 255)
        # input_data = input_data.astype(self.__model.data_type())
        # input_data = np.expand_dims(input_data, axis=0)
        return grey, main

    def detect_objects(self, image, algorithm_data):
        global rectangles

        logger = logging.getLogger()

        algorithm_data["name"] = "tflite"
        algorithm_data["tflite"] = {}

        interpreter = tflite.Interpreter(model_path=self._model_file_path, num_threads=4)
        interpreter.allocate_tensors()

        # TODO: Refactor this out to a separate method
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        height = input_details[0]["shape"][1]
        width = input_details[0]["shape"][2]
        floating_model = False
        if input_details[0]["dtype"] == np.float32:
            floating_model = True
        # END OF REFACTOR

        rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        initial_h, initial_w, channels = rgb.shape

        picture = cv2.resize(rgb, (width, height))

        input_data = np.expand_dims(picture, axis=0)
        if floating_model:
            input_data = (np.float32(input_data) - 127.5) / 127.5

        interpreter.set_tensor(input_details[0]["index"], input_data)

        interpreter.invoke()

        detected_boxes = interpreter.get_tensor(output_details[0]["index"])
        detected_classes = interpreter.get_tensor(output_details[1]["index"])
        detected_scores = interpreter.get_tensor(output_details[2]["index"])
        num_boxes = interpreter.get_tensor(output_details[3]["index"])

        rectangles = []
        for i in range(int(num_boxes)):
            top, left, bottom, right = detected_boxes[0][i]
            classId = int(detected_classes[0][i])
            score = detected_scores[0][i]
            if score > 0.2:
                xmin = left
                ymin = bottom
                xmax = right
                ymax = top
                box = [xmin, ymin, xmax, ymax]
                rectangles.append(box)
                if self._labels:
                    # print(self._labels[classId], 'score = ', score)
                    rectangles[-1].append(self._labels[classId])
                    algorithm_data["tflite"][self._labels[classId]] = score
                else:
                    # print('score = ', score)
                    algorithm_data["tflite"][classId] = score

        logger.debug(f"Detected {str(algorithm_data)}")

        # TODO: ALSO RETURN CLASSES AND SCORES
        return rectangles

    def get_object_detection_data(self, algorithm_data):
        return f" data:{str(algorithm_data)}"

    # TODO: REMOVE THIS IF ALL I'M DOING IS DOING str(algorithm_data)
    def print_algorithm_data(self, algorithm_data, motion_detected):
        logger = logging.getLogger()
        try:
            logger.debug(
                f"motion:{'TRUE' if motion_detected else '    '}"
                f" data:{str(algorithm_data):<40}",
            )
        except KeyError:
            logger.error("trouble printing tflite algorithm data")
