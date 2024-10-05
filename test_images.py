#!/usr/bin/python3

"""
Tests Models with images.  Used to debug and test the other classes.

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

IMG_DIR = "/home/admin/usbshare1/2_copy"
# IMG_DIR = "/home/admin/usbshare1/2_subset"
IMG_PATH = "/home/admin/usbshare1/2_copy/bravo-2024-09-21 22.50.39.00747-c0-M-n-Main_.jpg"

class RunModel:
    def __init__(self, model, option_preview=False, output_dir=None):
        self.__model = model
        self.__output_dir = output_dir
        self.__option_preview = option_preview

    def _resize_with_aspect_ratio(self, image, width=None, height=None, inter=cv2.INTER_AREA):
        dim = None
        (h, w) = image.shape[:2]

        if width is None and height is None:
            return image
        if width is None:
            r = height / float(h)
            dim = (int(w * r), height)
        else:
            r = width / float(w)
            dim = (width, int(h * r))

        return cv2.resize(image, dim, interpolation=inter)


    def process_image(self, image_path):
        logger = logging.getLogger()

        found_objects = []

        logger.info(f"Processing image: {image_path}")
        lores, main = self.__model.get_image_from_file(image_path)

        algorithm_data = {}
        rectangles, scores, classes = self.__model.detect_objects(lores, algorithm_data)
        self.__model.print_algorithm_data(algorithm_data, len(rectangles) > 0)

        img_width, img_height = main.shape[1], main.shape[0]
        logger.debug(f"Image width: {img_width} height: {img_height}")

        for i in range(0, len(rectangles)):
            rectangle_with_scores = rectangles[i] + [scores[i]]
            found_objects.append(rectangle_with_scores)

            # Potentially make drawing the rectangles on the image an option

            rect = rectangles[i]
            # rect_start = (int(rect[0] * 2 *img_width) - 5, int(rect[1] * 2 * img_height) - 5)
            # rect_end = (int(rect[2] * 2 * img_width) + 5, int(rect[3] * 2 * img_height) + 5)

            rect_start = (int(rect[0] *img_width) - 1, int(rect[1] * img_height) - 1)
            rect_end = (int(rect[2] * img_width) + 1, int(rect[3] * img_height) + 1)

            logger.debug(f"Rectangle start: {rect_start} end: {rect_end}") 

            cv2.rectangle(main, rect_start, rect_end, (0, 0, 255), 8)
            class_name = self.__model.class_name(int(classes[i]))
            cv2.putText(
                main,
                f"{int(int(classes[i]))}: {class_name} ({scores[i]:.2f})",
                (int(rect_start[0]), int(rect_start[1]) - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (0, 0, 255),
                2,
                cv2.LINE_AA,
            )

        if self.__option_preview: # potentially only display previews of windows with "hits"
            resize = self._resize_with_aspect_ratio(main, width=1280)
            cv2.imshow("Image Preview", resize)
            cv2.waitKey(2000)
            cv2.destroyAllWindows()

        if self.__output_dir:
            output_path = os.path.join(self.__output_dir, os.path.basename(image_path))
            cv2.imwrite(output_path, main)


        logger.info(f"Found objects: {found_objects}")

        return found_objects

    def process_directory(self):
        total_count = 0
        hit_count = 0

        for filename in os.listdir(IMG_DIR):
            total_count += 1

            img_path = os.path.join(IMG_DIR, filename)
            found_objcts = self.process_image(img_path)

            if len(found_objcts) > 0:
                hit_count += 1

        print(f"{self.__model.name()}: num_files {total_count} with_objects {hit_count}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)


    parser = argparse.ArgumentParser(
    prog="Process", description="Runs model on images."
)

    parser.add_argument("-p", "--preview", action="store_true")
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("-o", "--output", type=str, help="Directory to save output images")

    args = parser.parse_args()
    if args.preview:
        option_preview = True
    else:
        option_preview = False

    if args.debug:
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        logger.debug("Debugging enabled")

    if args.output:
        output_dir = args.output
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    # runner = RunModel(MobileObjectLocalizer()).process_directory()
    runner = RunModel(TensorFlowDetect(320, 240, 1152, 648, option_preview, 0.2), option_preview, output_dir).process_directory()
    # runner = RunModel(YOLOv5()).process_directory()

    print("Completed.")



