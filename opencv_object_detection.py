import cv2
import numpy as np

from image_saver import ImageSaver


class OpenCVObjectDetection:

    def __init__(self, config):
        """MotionDetector
        :param args: command line argumentstxttxt
        """
        self._config = config
        self._image_saver = ImageSaver()
        self._image_saver.set_config(config)

        self._net = cv2.dnn.readNetFromCaffe('MobileNetSSD_deploy.prototxt.txt', 'MobileNetSSD_deploy.caffemodel')
        self._classes = ["background", "aeroplane", "bicycle", "bird", "boat", "bottle", "bus", "car", "cat", "chair", "cow", "diningtable", "dog", "horse", "motorbike", "person", "pottedplant", "sheep", "sofa", "train", "tvmonitor"]

    # TODO: Determine whether we want to detect motion on the lores image for efficiency
    def detect_motion(self, current_array, previous_image, recording_time, algorithm_data):
        algorithm_data["name"] = "opencv"
        algorithm_data["opencv"] = {}

        three_channel = cv2.cvtColor(current_array, cv2.COLOR_RGBA2BGR)
        blob = cv2.dnn.blobFromImage(cv2.resize(three_channel, (300, 300)), 0.007843, (300, 300), 127.5)

        # Pass the blob through the network and get the detections
        self._net.setInput(blob)
        detections = self._net.forward()

        # Get the frame dimensions
        height, width = current_array.shape[:2]

        # Loop over the detections
        # TODO: Do we really need to loop over these?
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > 0.5:  # Filter weak detections
                class_id = int(detections[0, 0, i, 1])
                box = detections[0, 0, i, 3:7] * np.array([width, height, width, height])
                (startX, startY, endX, endY) = box.astype("int")

                print(f"Detected {self._classes[class_id]} with confidence {confidence:.2f}")
                algorithm_data['opencv']['class_id'] = class_id
                algorithm_data['opencv']['confidence'] = confidence

        if detections.shape[2] > 0:
            return True
        else:
            return False

    def print_algorithm_data(self, algorithm_data, motion_detected):
        try:
            print(
                f"motion:{'TRUE' if motion_detected else '    '}"
                f" min_hist_def:{algorithm_data['opencv']['class_id']}"
                f" min_hist_def:{algorithm_data['opencv']['confidence']}",
                end="\r",
            )
        except KeyError:
            print("trouble printing opencv algorithm data")
