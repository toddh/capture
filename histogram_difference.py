from PIL import ImageFilter
from image_saver import ImageSaver


class HistogramDifference:
    """Detect motion and store snapshots based on a difference in the Histogram."""

    def __init__(self, config):
        """MotionDetector
        :param args: command line arguments
        """
        self._config = config
        self._image_saver = ImageSaver()
        self._image_saver.set_config(config)

    # TODO: Determine whether we want to detect motion on the lores image for efficiency
    def detect_motion(self, current_image, previous_image, recording_time, algorithm_data):
        algorithm_data["name"] = "histogram"

        if self._config["histogram"]["blur"]:
            current_image = current_image.filter(
                ImageFilter.GaussianBlur(self._config["histogram"]["radius"])
            )
            previous_image = previous_image.filter(
                ImageFilter.GaussianBlur(self._config["histogram"]["radius"])
            )
        # TODO: Improve efficiency by saving the blurred previous image for next iteration

        current_hist = current_image.histogram()
        previous_hist = previous_image.histogram()

        hist_diff = sum(
            [abs(c - p) for c, p in zip(current_hist, previous_hist)]
        ) / len(current_hist)

        algorithm_data["hist_diff"] = hist_diff

        if self._config['histogram']['save_intermediate_images']:
            self._image_saver.save_intermediate_image(current_image, recording_time, algorithm_data)

        if hist_diff > self._config["histogram"]["min_hist_diff"]:
            return True
        else:
            return False

    def print_algorithm_data(self, algorithm_data, motion_detected):
        print(
            f"motion:{'TRUE' if motion_detected else '    '}"
            f" blur:{'TRUE' if self._config['histogram']['blur'] else '    '}"
            f" min_hist_def:{self._config['histogram']['min_hist_diff']}"
            f" hist_diff:{algorithm_data['hist_diff']:04.0f}",
            end="\r",
        )
