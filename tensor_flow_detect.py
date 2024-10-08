import logging
import pprint

import cv2
import numpy as np
import tflite_runtime.interpreter as tflite
from picamera2 import MappedArray, Picamera2, Preview
from libcamera import Transform

rectangles = []
main_buffer_width = None
main_buffer_height = None

def draw_rectangles_preview(request):
    # NOTE: THIS IS NOT PART OF OUR CLASS!
    #
    # The MappedArray needs to be given a request and the name of the stream for which we
    # want access to its image buffer. It then maps that memory into user space and presents it
    # to us as a regular numpy array, just as if we had obtained it via capture_array. Once we
    # leave the with block, the memory is unmapped and everything is cleaned up.

    for rect in rectangles:
        with MappedArray(request, "main") as m:
            for rect in rectangles:
                xmin = rect[0] * main_buffer_width
                ymin = rect[1] * main_buffer_height
                xmax = rect[2] * main_buffer_width
                ymax = rect[3] * main_buffer_height

                rect_start = (int(xmin) - 1, int(ymin) - 1)
                rect_end = (int(xmax) + 1, int(ymax) + 1)
                # rect_start = (int(xmin * 2) - 5, int(ymin * 2) - 5)
                # rect_end = (int(xmax * 2) + 5, int(ymax * 2) + 5)


                cv2.rectangle(m.array, rect_start, rect_end, (0, 0, 255), 8)
                if len(rect) == 5:
                    text = rect[4]
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    cv2.putText(
                        m.array,
                        text,
                        (int(rect_start[0]), int(rect_start[1]) - 10),
                        font,
                        1,
                        (0, 0, 255),
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
# $ sudo apt install build-essential255
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

    def __init__(self, config, flip, preview):
        global rectangles
        global main_buffer_width
        global main_buffer_height

        self._labels = self._read_label_file("coco_labels.txt")
        self._model_file_path = "mobilenet_v2.tflite"

        self._main_width = config['main_width']
        self._main_height = config['main_height']
        self._lores_width = config['lores_width']
        self._lores_height = config['lores_height']
        self._threshold = config['threshold']
        self._draw_rectangles = config['draw_rectangles']

        self._flip = flip
        self._preview = preview
        
        rectangles = []
        main_buffer_width = config['main_width']
        main_buffer_height = config['main_height']

    def name(self):
        return self._model_file_path
    
    def _read_label_file(self, file_path):
        with open(file_path, "r") as f:
            lines = f.readlines()
        ret = {}
        for line in lines:
            pair = line.strip().split(maxsplit=1)
            ret[int(pair[0])] = pair[1].strip()
        return ret
    
    def class_name(self, class_id):
        return self._labels[class_id]

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

        if self._flip:
            transform = Transform(vflip=True, hflip=True)
        else:
            transform = Transform()

        config = picam2.create_preview_configuration(
            transform=transform,
            main={"size": (self._main_width, self._main_height)},
            lores={"size": (self._lores_width, self._lores_height), "format": "YUV420"},
            display="main",
        )

        picam2.configure(config)

        self._stride = picam2.stream_configuration("lores")["stride"]
        # Stride = The length of each row of the image in bytes

        if self._draw_rectangles:
            picam2.post_callback = draw_rectangles_preview

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
        grey = cv2.resize(grey, (self._lores_width, self._lores_height)) # FIXME: Maybe this should just be the size we want to send into the model.

        return grey, img

    def detect_objects(self, image):
        global rectangles

        logger = logging.getLogger()

        logger.debug("detect_objects-")
        logger.debug(f"image shape prior to modifying: {image.shape}")
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
        # I think that at this point, picture needs to be
        logger.debug("picture shape: " + str(picture.shape))

        input_data = np.expand_dims(picture, axis=0)
        if floating_model:
            input_data = (np.float32(input_data) - 127.5) / 127.5

        logger.debug("input_data shape: " + str(input_data.shape))

        interpreter.set_tensor(input_details[0]["index"], input_data)

        interpreter.invoke()

        detected_boxes = interpreter.get_tensor(output_details[0]["index"])
        detected_classes = interpreter.get_tensor(output_details[1]["index"])
        detected_scores = interpreter.get_tensor(output_details[2]["index"])
        num_boxes = interpreter.get_tensor(output_details[3]["index"])

        logger.debug(f"detected_boxes shape: {detected_boxes.shape}")
        logger.debug(f"detected_classes shape: {detected_classes.shape} {pprint.pformat(detected_classes)}")
        logger.debug(f"detected_scores shape: {detected_scores.shape} {pprint.pformat(detected_scores)}")

        rectangles = []
        scores = []
        classes = []

        for i in range(int(num_boxes)):
            top, left, bottom, right = detected_boxes[0][i]
            classId = int(detected_classes[0][i])
            score = detected_scores[0][i]
            if score > self._threshold:
                xmin = left
                ymin = bottom
                xmax = right
                ymax = top
                box = [xmin, ymin, xmax, ymax]
                logger.debug(f"appending box: {box}")
                rectangles.append(box)
                scores.append(detected_scores[0][i])
                classes.append(detected_classes[0][i])
                if self._labels:
                    rectangles[-1].append(self._labels[classId])

        # logger.debug(f"Detected {str(algorithm_data)}")

        # Seems like rectangles are bottom-left then top-right
        return rectangles, scores, classes

    def get_object_detection_data(self, algorithm_data):
        return f" data:{str(algorithm_data)}"
