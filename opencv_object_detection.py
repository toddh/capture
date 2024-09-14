import cv2
import numpy as np
import logging

from image_saver import ImageSaver

from  stats_file import accumulate_stats

class OpenCVObjectDetection:
    """
    Uses OpenCV to detect objects in the image.  This is a simple object detection algorithm that uses a pre-trained model.
    """

    def __init__(self, config):
        self._config = config
        self._image_saver = ImageSaver()
        self._image_saver.set_config(config)

        # TODO: See if there is a better model for us to use
        self._net = cv2.dnn.readNetFromCaffe('MobileNetSSD_deploy.prototxt.txt', 'MobileNetSSD_deploy.caffemodel')
        self._classes = ["background", "aeroplane", "bicycle", "bird", "bottle", "bus", "car", "cat", "chair", "cow", "diningtable", "dog", "horse", "motorbike", "person", "sheep", "sofa", "train", "tvmonitor"]

    # TODO: Determine whether we want to detect motion on the lores image for efficiency
    def detect_motion(self, current_array, recording_time, algorithm_data):
        logger = logging.getLogger()

        algorithm_data["name"] = "opencv"
        algorithm_data["opencv"] = {}

        three_channel = cv2.cvtColor(current_array, cv2.COLOR_RGBA2BGR)
        blob = cv2.dnn.blobFromImage(cv2.resize(three_channel, (300, 300)), 0.007843, (300, 300), 127.5)

        if self._config['capture']['save_intermediate_images']:
            self._image_saver.save_intermediate_array(three_channel, recording_time, self.get_object_detection_data(algorithm_data))

        self._net.setInput(blob)
        detections = self._net.forward()
        height, width = current_array.shape[:2]

        cnt = 0

        n = detections.shape[2]

        if n > 0:
            # TODO: Figure out why get 100 items back
            for i in range(n):
                # algorithm_data['opencv'][i] = {}

                confidence = detections[0, 0, i, 2]
                if confidence > 0.5:  # Filter weak detections
                    class_id = int(detections[0, 0, i, 1])

                    if self._config['opencv']['preview']:
                        box = detections[0, 0, i, 3:7] * np.array([width, height, width, height])
                        (startX, startY, endX, endY) = box.astype("int")

                        label = f"{self._classes[class_id]}: {confidence:.2f}"
                        cv2.rectangle(current_array, (startX, startY), (endX, endY), (0, 255, 0), 2)
                        y = startY - 15 if startY - 15 > 15 else startY + 15
                        cv2.putText(current_array, label, (startX, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                        cv2.imshow('Object Detection', current_array)
                        cv2.waitKey(1)
                        # TODO: Figure out a non-blocking way to do this
                        # if cv2.waitKey(1) & 0xFF == ord('q'):
                        #     break

                    # print(f"Detected {self._classes[class_id]} with confidence {confidence:.2f}")
                    algorithm_data['opencv'][self._classes[class_id]] = confidence
                    cnt += 1

        logger.debug(f"Detected {cnt} objects")


        accumulate_stats(recording_time, 0)

        if cnt > 0:
            return True
        else:
            return False

    def print_algorithm_data(self, algorithm_data, motion_detected):
        try:
            print(
                f"motion:{'TRUE' if motion_detected else '    '}"
                f" data:{str(algorithm_data):<40}",
            )
        except KeyError:
            print("trouble printing opencv algorithm data")

    def get_object_detection_data(self, algorithm_data):
        return f" data:{str(algorithm_data)}"

    def cleanup(self):
        if self._config["preview"]["enable"]:
            cv2.destroyAllWindows()
