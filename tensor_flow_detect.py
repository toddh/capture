import numpy as np
import cv2
import tflite_runtime.interpreter as tflite
from picamera2 import MappedArray, Picamera2, Preview


rectangles = []

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
                print(rect)
                rect_start = (int(rect[0] * 2) - 5, int(rect[1] * 2) - 5)
                rect_end = (int(rect[2] * 2) + 5, int(rect[3] * 2) + 5)
                cv2.rectangle(m.array, rect_start, rect_end, (0, 255, 0, 0))
                if len(rect) == 5:
                    text = rect[4]
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    cv2.putText(m.array, text, (int(rect[0] * 2) + 10, int(rect[1] * 2) + 10),
                                    font, 1, (255, 255, 255), 2, cv2.LINE_AA)



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

    def __init__(self, config):
        global rectangles

        self._labels = self.read_label_file("coco_labels.txt")
        self._model_file_path = "mobilenet_v2.tflite"
        self._normalSize = (640, 480)
        self._lowresSize = (320, 240)
        self._model = 'mobilenet_v2.tflite'

        rectangles = []


    def read_label_file(self, file_path):
            with open(file_path, 'r') as f:
                lines = f.readlines()
            ret = {}
            for line in lines:
                pair = line.strip().split(maxsplit=1)
                ret[int(pair[0])] = pair[1].strip()
            return ret

    def start_camera(self, camera_num):
        picam2 = Picamera2(camera_num)
        picam2.start_preview(Preview.QTGL)
        config = picam2.create_preview_configuration(main={"size": self._normalSize},
                                                    lores={"size": self._lowresSize, "format": "YUV420"})
        picam2.configure(config)

        self._stride = picam2.stream_configuration("lores")["stride"]
        picam2.post_callback = draw_rectangles

        picam2.start()

        return picam2
    
    def get_image(self, picam2):
        buffer = picam2.capture_buffer("lores")
        # TODO: Figure out what's going on here
        grey = buffer[:self._stride * self._lowresSize[1]].reshape((self._lowresSize[1], self._stride))

        return grey

    def InferenceTensorFlow(self, image):
        global rectangles

        interpreter = tflite.Interpreter(model_path=self._model_file_path, num_threads=4)
        interpreter.allocate_tensors()

        # TODO: Refactor this out to a separate metho
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        height = input_details[0]['shape'][1]
        width = input_details[0]['shape'][2]
        floating_model = False
        if input_details[0]['dtype'] == np.float32:
            floating_model = True
        # END OF REFACTOR

        rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        initial_h, initial_w, channels = rgb.shape

        picture = cv2.resize(rgb, (width, height))

        input_data = np.expand_dims(picture, axis=0)
        if floating_model:
            input_data = (np.float32(input_data) - 127.5) / 127.5

        interpreter.set_tensor(input_details[0]['index'], input_data)

        interpreter.invoke()

        detected_boxes = interpreter.get_tensor(output_details[0]['index'])
        detected_classes = interpreter.get_tensor(output_details[1]['index'])
        detected_scores = interpreter.get_tensor(output_details[2]['index'])
        num_boxes = interpreter.get_tensor(output_details[3]['index'])

        rectangles = []
        for i in range(int(num_boxes)):
            top, left, bottom, right = detected_boxes[0][i]
            classId = int(detected_classes[0][i])
            score = detected_scores[0][i]
            if score > 0.5:
                xmin = left * initial_w
                ymin = bottom * initial_h
                xmax = right * initial_w
                ymax = top * initial_h
                box = [xmin, ymin, xmax, ymax]
                rectangles.append(box)
                if self._labels:
                    # print(self._labels[classId], 'score = ', score)
                    rectangles[-1].append(self._labels[classId])
                else:
                    # print('score = ', score)
                    pass

        return len(rectangles)
    
    def get_object_detection_data(self, algorithm_data):
        return f" data:{str(algorithm_data)}"
