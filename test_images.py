#!/usr/bin/python3

"""
Tests Models with images

"""

# The following line gets over the fact that setuptools isn't part of python 3.12. Tflite seems to require this.
# See https://stackoverflow.com/a/78136410
# import setuptools.dist

import argparse
import logging
import os
from pprint import pprint

import cv2

from tensor_flow_detect import TensorFlowDetect

# IMG_DIR = "/home/admin/usbshare1/2_copy"
IMG_DIR = "/home/admin/usbshare1/easy_images"
IMG_PATH = "/home/admin/usbshare1/2_copy/bravo-2024-09-21 22.50.39.00747-c0-M-n-Main_.jpg"

option_preview = True

class RunModel:
    def __init__(self, model):
        self.__model = model

    def process_image(self, image_path):
        lores, main = self.__model.get_image_from_file(image_path)

        algorithm_data = {}
        rectangles = self.__model.detect_objects(lores, algorithm_data)
        self.__model.print_algorithm_data(algorithm_data, len(rectangles) > 0)

        img_width, img_height = main.shape[1], main.shape[0]

        for i in range(0, len(rectangles)):
            if True:   # WAS detection_scores[i] > 0.2:
                # pprint(detection_boxes)
                # x = rectangles[i, [1, 3]] * img_width
                # efficient_det: detection_boxes shape = (25,4)
                # kh_yolo5: an array of arrays.
                # x = [1, 1]
                # x[0] = detection_boxes[i, 1] * img_width
                # x[1] = detection_boxes[i, 3] * img_width

                # y = rectangles[i, [0, 2]] * img_height
                # y = [1, 1]
                # y[0] = detection_boxes[i, 0] * img_width
                # y[1] = detection_boxes[i, 2] * img_width

                # rectangle = [x[0], y[0], x[1], y[1]]
                # class_id = detection_classes[i]
                # print(f"{i}: Class: {class_id} score: {detection_scores[0, i]} box: ({str(rectangle)})")
                # datum.append(
                #     {"class_id": class_id, "score": float(detection_scores[i]), "rectangle": str(rectangle)}
                # )
                if option_preview:
                    rect = rectangles[i]
                    print(rect)
                    rect_start = (int(rect[0] * 2 *img_width) - 5, int(rect[1] * 2 * img_height) - 5)
                    rect_end = (int(rect[2] * 2 * img_width) + 5, int(rect[3] * 2 * img_height) + 5)

                    cv2.rectangle(main, rect_start, rect_end, (0, 255, 0), 2)
                    # class_name = self.__model.class_name(int(class_id))
                    # cv2.putText(
                    #     img,
                    #     f"{int(class_id)}: {class_name} ({detection_scores[i]:.2f})",
                    #     (int(x[0]), int(y[0]) - 10),
                    #     cv2.FONT_HERSHEY_SIMPLEX,
                    #     0.75,
                    #     (0, 255, 0),
                    #     2,
                    #     cv2.LINE_AA,
                    # )


        if option_preview: # WAS and len(datum) > 0:
            cv2.imshow(f"Image Preview", main)
            cv2.waitKey(5000)
            cv2.destroyAllWindows()

        return 0

    def process_directory(self):
        stats = []

        for filename in os.listdir(IMG_DIR):
            img_path = os.path.join(IMG_DIR, filename)
            datum = self.process_image(img_path)

            stats.append(datum)

        # cnt = 0
        # for datum in stats:
        #     if len(datum) > 0:
        #         cnt += 1

        # for datum in stats:
        #     print(str(datum))

        # print(f"{self.__model.name()}: num_files {len(stats)} with_objects {cnt}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)


    parser = argparse.ArgumentParser(
    prog="Process", description="Runs model on images."
)

    parser.add_argument("-p", "--preview", action="store_true")
    parser.add_argument("-d", "--debug", action="store_true")

    args = parser.parse_args()
    if args.preview:
        option_preview = True

    if args.debug:
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        logger.debug("Debugging enabled")

    # runner = RunModel(MobileObjectLocalizer()).process_directory()
    runner = RunModel(TensorFlowDetect(320, 240, 1152, 648, option_preview)).process_directory()
    # runner = RunModel(YOLOv5()).process_directory()

    print("Completed.")



