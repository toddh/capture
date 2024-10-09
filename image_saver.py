import logging
import platform

import piexif
import piexif.helper

from PIL import Image
from PIL.ExifTags import TAGS

from capture_data import CaptureData


def get_exif_tag_id(tag_name):
    for tag_id, name in TAGS.items():
        if name == tag_name:
            return tag_id
    return None


def singleton(cls):
    instances = {}  # Dictionary to store the single instance

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


@singleton
class ImageSaver:
    def __init__(self):
        self.__directory = None
        self._logger = logging.getLogger()

    def set_config(self, config):
        self._config = config

    def format_exif(self, capture_data):
        logger = logging.getLogger()

        user_comment = capture_data.to_json()
        logger.info(f"User Comment: {user_comment}")

        formatted_comment = piexif.helper.UserComment.dump(str(user_comment))

        formatted_model = capture_data.to_short_string().encode()

        time_str = capture_data.capture_time_str()

        zeroth_ifd = {
            piexif.ImageIFD.Make: "Camera Module 3",
            piexif.ImageIFD.Model: formatted_model,
        }
        exif_ifd = {
            piexif.ExifIFD.DateTimeOriginal: time_str,  # FIXME: Should this be a string?
            piexif.ExifIFD.UserComment: formatted_comment,
        }
        gps_ifd = {}
        first_ifd = {}

        exif_dict = {
            "0th": zeroth_ifd,
            "Exif": exif_ifd,
            "GPS": gps_ifd,
            "1st": first_ifd,
        }
        exif_bytes = piexif.dump(exif_dict)

        return exif_bytes

    def format_file_name(self, node, capture_time_str, camera_num, motion_detected, pir, stream_name):
        file_name = (
            f"{self._config['capture']['output_dir']}{node}-"
            f"{capture_time_str}-"
            f"c{camera_num}-"
            f"{'M' if motion_detected else 'm'}"
            f"{'P' if pir else 'p'}-"
            f"{stream_name:_<5s}.jpg"
        )

        return file_name

    def save_array(
        self,
        lores_array,
        main_array,
        capture_data,
    ):
        """Save an array. Either intermediate or final.

        Args:
            lowres_array (_type_): The Array received from picamera2 get array
            hires_array (_type_): The Array received from picamera2 get array
            capture_time (datetime): When was the image taken
            motion_detected (boolean?): Did the algorithm detect motion.  Could be None if we don't know.
            pir (boolean?): Did the PIR detect motion. Could be None if we don't know.
            camera_num (string): What stream is this? "lores" or "main"
            image_tag (char): Where does this come from in the processing chain? 'd' = detection image, 'i' = intermediate image, 't' = timed image
            algorithm_data (ditectionary): dictionary of data from the algorithm.
        """
        try:
            if self._config["capture"]["save_images"]:
                exif_bytes = self.format_exif(capture_data)

                # image = Image.fromarray(lores_array).convert("RGB")
                # file_name = self.format_file_name(
                #     platform.node(), capture_time, str(camera_num), motion_detected, pir, "lores"
                # )
                # image.save(file_name, exif=exif_bytes)

                image = Image.fromarray(main_array).convert("RGB")
                file_name = self.format_file_name(
                    platform.node(),
                    capture_data.capture_time_str(),
                    str(capture_data.camera_num),
                    capture_data.object_detected,
                    capture_data.pir_fired,
                    "Main",  # Make it a capital M so it sorts before the lores stream
                )
                image.save(file_name, exif=exif_bytes)

        except Exception as e:
            self._logger.error(f"An error occurred saving the image: {e}")
