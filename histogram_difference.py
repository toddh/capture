from PIL import Image
from PIL import ImageFilter

from image_saver import ImageSaver

class HistogramDifference:
    """Detect motion and store snapshots based on a difference in the Histogram."""

    def __init__(self, config, picam2):
        """MotionDetector
        :param args: command line arguments
        """

        # TODO: Move the configuration information into a separate class.
        self.__min_pixel_diff = config["histogram"]["min_pixel_diff"]
        self.__blur = config["histogram"]["blur"]
        self.__lores_width = config["histogram"]["width"]
        self.__lores_height = config["histogram"]["height"]

        self.__max_time_since_last_detection_seconds = config["capture"]["anyways"]

        self.__time_of_last_image = None
        self.__picam2 = picam2
        self.__time_of_last_image = None

        self.__image_saver = ImageSaver()

    # def loop(self):

    #     previous_frame = None
    #     self.__time_of_last_image = datetime.datetime.now()
    #     detection_count = 0

    #     while True:
    #         try:
    #             current_frame = self.__picam2.capture_buffer("lores")
    #             # capture_buffer returns a 1d array.  This makes it a 2D array.  Picamera2 does have a helper make_array. Why don't we use that?
    #             # And we're doing lores, I assume to make the math easier.  Shouldn't we configure the camera that way?
    #             current_frame = current_frame[:self.__lores_width * self.__lores_height].reshape(self.__lores_height, self.__lores_width)

    #             if previous_frame is not None:

    #                 # Potential location to draw the boundary.  Inputs: current_frame, previous_frame. Output is whether to save or not.
    #                 # May need to pass some information about times, and status information on algorithm calculations, etc.
    #                 # Other items are specific to the algorithm.
    #                 hist_diff = self.__calculate_histogram_difference(current_frame, previous_frame, self.__blur, detection_count % self.__save_every == 0)
    #                 if hist_diff > self.__min_pixel_diff:
    #                     logging.info(f"start capturing at: {datetime.datetime.now()}")
    #                     self.__image_saver.capture(True, hist_diff)
    #                     self.__time_of_last_image = datetime.datetime.now()
    #                 else:
    #                     if self.__is_max_time_since_last_motion_detection_exceeded():
    #                         logging.info("max time since last motion detection exceeded")
    #                         self.__image_saver.capture(False, hist_diff)
    #                         self.__time_of_last_image = datetime.datetime.now()
    #             previous_frame = current_frame
    #             detection_count += 1
    #         except Exception as e:
    #             logging.error(f"An error occurred in the motion detection loop: {e}")
    #             continue

    def detect_motion(self, current_frame, previous_frame, meta_data):

        meta_data["algorithm"] = "histogram"

        if self.__blur:
            current_image = Image.fromarray(current_frame).filter(ImageFilter.GaussianBlur(1))
            previous_image = Image.fromarray(previous_frame).filter(ImageFilter.GaussianBlur(1))
        else:
            current_image = Image.fromarray(current_frame)
            previous_image = Image.fromarray(previous_frame)

        current_hist = current_image.histogram()
        previous_hist = previous_image.histogram()

        hist_diff = sum([abs(c - p) for c, p in zip(current_hist, previous_hist)]) / len(current_hist)

        # logging.info(f"hist_diff: {hist_diff}")
        if hist_diff > self.__min_pixel_diff:
            return True
        else:
            return False
