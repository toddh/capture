import yaml
import numpy as np
import tensorflow as tf
import abstract_object_detector
import kagglehub
import cv2

class EfficientDet(abstract_model.AbstractObjectDetector):
    """https://www.kaggle.com/models/tensorflow/efficientdet/tfLite

    Args:
        abstract_model (_type_): _description_
    """

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


def __init__(self, config):
    super().__init__(config)

    self._model_path = "tensorflow/efficientdet/tfLite/lite2-detection-default"

    self._model_name = "1.tflite"  # If lite4, it's 2.tflite
    self._class_names = []

    with open("coco_labels.txt", "r") as file:
        self._class_names = [line.strip() for line in file.readlines()]

    self._path = kagglehub.model_download(self.__model.model_path())
    self._file_name = self._path + "/" + self.__model.model_name()

    with open(self._file_name, "rb") as f:
        model_content = f.read()
    self._interpreter = tf.lite.Interpreter(model_content=model_content)

    self._interpreter.allocate_tensors()
    self._input_details = self._interpreter.get_input_details()
    self._output_details = self._interpreter.get_output_details()
    self._input_shape = self._input_details[0]["shape"]
    self._class_names = self.__model.class_names()
    self.__model.process_model(self._input_details, self._output_details)

    self._option_preview

def preprocess_image(self, img, input_shape):
    input_data = cv2.resize(img, (input_shape[1], input_shape[2]))
    input_data = cv2.cvtColor(input_data, cv2.COLOR_BGR2RGB)  # TODO: Figure out if I'm always doing this right
    input_data = np.clip(input_data, 0, 255)
    input_data = input_data.astype(self.__model.data_type())
    input_data = np.expand_dims(input_data, axis=0)
    return input_data

def detect_motion(self, current_array, recording_time, algorithm_data):
    img = convert current_array to img
    img_height, img_width, _ = img.shape
    input_data = self.preprocess_image(img, self._input_shape)

    self._interpreter.set_tensor(self._input_details[0]["index"], input_data)
    self._interpreter.invoke()

    # The TFLite_Detection_PostProcess custom op node has four outputs. THIS IS ONLY TRUE FOR SOME MODELS.
    #
    # detection_boxes: a tensor of shape [1, num_boxes, 4] with normalized coordinates
    # detection_scores: a tensor of shape [1, num_boxes]
    # detection_classes: a tensor of shape [1, num_boxes] containing class prediction for each box
    # num_boxes: a tensor of size 1 containing the number of detected boxes
    # From https://github.com/tensorflow/tensorflow/issues/34761

    datum = []

    detection_boxes, detection_scores, detection_classes, num_boxes = self.__model.get_results(self._interpreter, self._output_details)
    #
    # Using efficient_det to double check outputs, here's what I get:
    # detection_boxes is an array (NOT A TENSOR) shape (25, 4) - values are nomarmalized between 0 and 1
    #   They should be in the form of [xmin, ymin, xmax, ymax]
    # detection_scores is an array (NOT A TENSOR) shape (25, ) - scores are between 0 and 1
    # detection_classes is an array (NOT A TENSOR) shape (25, ) - values are 17.0, 17.0, 32,0, 0.0 etc.....
    # num_boxes is an integer = 25
    # (I think the 25 is the number of output nodes in the neural network.)
    #
    # Mobilenet_object detection is similar
    # detection_boxes shape (100, 4)
    # detection_classes = (100,) - I think mmobile_net_object_detectiojn this will always be zero - it doesn't identify
    # detection_soces is shape (100,)
    # num_boxes is an integer = 100

    for i in range(0, num_boxes):
        if detection_scores[i] > 0.2:
            x = detection_boxes[i, [1, 3]] * img_width
            y = detection_boxes[i, [0, 2]] * img_height

            rectangle = [x[0], y[0], x[1], y[1]]
            class_id = detection_classes[i]

            datum.append(
                {"class_id": class_id, "score": float(detection_scores[i]), "rectangle": str(rectangle)}
            )
            if self._option_preview:
                cv2.rectangle(img, (int(x[0]), int(y[0])), (int(x[1]), int(y[1])), (0, 255, 0), 2)
                class_name = self.__model.class_name(int(class_id))
                cv2.putText(
                    img,
                    f"{int(class_id)}: {class_name} ({detection_scores[i]:.2f})",
                    (int(x[0]), int(y[0]) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.75,
                    (0, 255, 0),
                    2,
                    cv2.LINE_AA,
                )


    if self._option_preview and len(datum) > 0:
        cv2.imshow(f"Found {len(datum)} classes", img)
        cv2.waitKey(1500)
        cv2.destroyAllWindows()

    return datum
