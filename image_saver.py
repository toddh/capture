import logging
import platform

import piexif
from PIL import Image
from PIL.ExifTags import TAGS


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

    def format_exif(
        self, image_time, camera_name, motion_detected, pir, algorithm_data
    ):
        user_comment = {}
        user_comment["camera_name"] = camera_name
        user_comment["motion_detected"] = motion_detected
        user_comment["pir"] = pir
        user_comment["algorithm_data"] = algorithm_data

        formatted_comment = piexif.helper.UserComment.dump(str(user_comment))

        formatted_model = f"{'PIR' if pir else 'NoPIR'} - {'MOTION' if motion_detected else 'NoMotion'}".encode()

        time_str = image_time.strftime("%Y:%m:%d %H:%M:%S")

        zeroth_ifd = {
            piexif.ImageIFD.Make: u"Camera Module 3",
            piexif.ImageIFD.Model: formatted_model
        }
        exif_ifd = {
            piexif.ExifIFD.DateTimeOriginal: time_str,
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

    def save_array(self, array, recording_time, motion_detected, pir, algorithm_data):
        if motion_detected:
            file_name = f"{self._config['capture']['output_dir']}{platform.node()}-{recording_time:%Y-%m-%d %H%M%S}.{recording_time.microsecond // 1000:05d}-d.jpg"
        else:
            file_name = f"{self._config['capture']['output_dir']}{platform.node()}-{recording_time:%Y-%m-%d %H%M%S}.{recording_time.microsecond // 1000:05d}.jpg"

        image = Image.fromarray(array).convert("RGB")

        try:
            if self._config["capture"]["save_images"]:

                exif_bytes = self.format_exif(
                    self._config["capture"]["camera_name"],
                    motion_detected,
                    pir,
                    algorithm_data,
                )

                image.save(file_name, exif=exif_bytes)
        except Exception as e:
            self._logger.error(f"An error occurred saving the image: {e}")

    def save_intermediate_array(self, array, recording_time, algorithm_data):
        file_name = f"{self._config['capture']['output_dir']}{platform.node()}-{recording_time:%Y-%m-%d %H%M%S}.{recording_time.microsecond // 1000:05d}-1.jpg"

        image = Image.fromarray(array).convert("RGB")

        try:
            if self._config["capture"]["save_images"]:
                exif_bytes = self.format_exif(
                    self._config["capture"]["camera_name"],
                    False,
                    False,
                    algorithm_data,
                )

                image.save(file_name, exif=exif_bytes)
        except Exception as e:
            self._logger.error(f"An error occurred saving the image: {e}")

    # def save_image(self, image, recording_time, motion_detected, algorithm_data):
    #     if motion_detected:
    #         file_name = f"{self._config['capture']['output_dir']}{recording_time:%Y-%m-%d %H%M%S}.{recording_time.microsecond // 1000:05d}-d.jpg"
    #     else:
    #         file_name = f"{self._config['capture']['output_dir']}{recording_time:%Y-%m-%d %H%M%S}.{recording_time.microsecond // 1000:05d}.jpg"

    #     try:
    #         if self._config["capture"]["save_images"]:
    #             # This link was useful for this. I had trouble just using PILLOW. https://stackoverflow.com/a/63649983
    #             txt = f"1234578 {algorithm_data['hist_diff']:.0f}\n"
    #             exif_ifd = {piexif.ExifIFD.UserComment: txt.encode()}

    #             exif_dict = {"0th": {}, "Exif": exif_ifd, "1st": {},
    #                     "thumbnail": None, "GPS": {}}

    #             exif_dat = piexif.dump(exif_dict)
    #             image.save(file_name, exif=exif_dat)
    #     except Exception as e:
    #         logging.error(f"An error occurred saving the image: {e}")

    # def save_intermediate_image(self, image, recording_time, algorithm_data):
    #     file_name = f"{self._config['capture']['output_dir']}{recording_time:%Y-%m-%d %H%M%S}.{recording_time.microsecond // 1000:05d}-2.jpg"

    #     try:
    #         image.save(file_name)
    #     except Exception as e:
    #         logging.error(f"An error occurred saving the image: {e}")

    # def save_intermediate_images(self, current_image, previous_image, recording_time, algorithm_data):
    #     current_file_name = f"{self._config['capture']['output_dir']}{recording_time:%Y-%m-%d %H%M%S}.{recording_time.microsecond // 1000:05d}-2.jpg"
    #     previous_file_name = f"{self._config['capture']['output_dir']}{recording_time:%Y-%m-%d %H%M%S}.{recording_time.microsecond // 1000:05d}-1.jpg"

    #     try:
    #         # txt = f"1234578 {algorithm_data['hist_diff']:.0f}\n"
    #         txt = "1234579Data will go here\n"
    #         exif_ifd = {piexif.ExifIFD.UserComment: txt.encode()}

    #         exif_dict = {"0th": {}, "Exif": exif_ifd, "1st": {},
    #                 "thumbnail": None, "GPS": {}}

    #         exif_dat = piexif.dump(exif_dict)

    #         current_image.save(current_file_name, exif=exif_dat)
    #         previous_image.save(previous_file_name,  exif=exif_dat)

    #     except Exception as e:
    #         logging.error(f"An error occurred saving the image: {e}")
