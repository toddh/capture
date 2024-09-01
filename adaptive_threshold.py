import cv2
import numpy as np
from PIL import Image
from PIL import ImageFilter


class AdaptiveThreshold:
    def __init__(self, config):
        self._config = config

    def detect_motion(self, current_image, previous_image, algorithm_data):
        """
        Detect motion between two frames."""

        algorithm_data["name"] = "adaptive_threshold"

        # TODO: Determine how to make this more robust. What happens if we change the format of image we are capturing?
        # TODO: Do we need to convert to a numpy array?

        if self._config["adaptive_threshold"]["blur"]:
            current_image = current_image.filter(ImageFilter.GaussianBlur(75))
            previous_image = previous_image.filter(ImageFilter.GaussianBlur(75))
        # TODO: Determine if this is necessary with adaptive thresholding

        # Convert PIL images to NumPy arrays if necessary
        if isinstance(current_image, Image.Image):
            current_image = np.array(current_image)
        if isinstance(previous_image, Image.Image):
            previous_image = np.array(previous_image)

        # Debugging: Check if images are valid
        if current_image is None or previous_image is None:
            raise ValueError("One of the input images is None")

        gray1 = cv2.cvtColor(current_image, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(previous_image, cv2.COLOR_BGR2GRAY)

        diff = cv2.absdiff(gray1, gray2)

        # zeros = np.zeros(gray1.shape, np.uint8)

        thresh = cv2.adaptiveThreshold(
            diff, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 5, -2
        )
        # TODO: Figure out why we are using -2 rather than +2.

        # thresh_zeros = cv2.adaptiveThreshold(
        #     zeros, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 21, -1
        # )

        cv2.imwrite("thresh.jpg", thresh)
        # cv2.imwrite("thresh_zeros.jpg", thresh_zeros)

        total_pixels = thresh.size
        changed_pixels = np.count_nonzero(thresh)
        change_percentage = (changed_pixels / total_pixels) * 100

        # changed_pixels_zeros = np.count_nonzero(thresh_zeros)

        algorithm_data["changed_pixels"] = changed_pixels
        algorithm_data["change_percentage"] = change_percentage

        if change_percentage > self._config["adaptive_threshold"]["threshold_percent"]:
            return True
        else:
            return False

    def print_algorithm_data(self, algorithm_data, motion_detected):
        print(
            f"motion:{'TRUE' if motion_detected else '    '} changed_pixels:{algorithm_data['changed_pixels']}",
            end="\r",
        )
