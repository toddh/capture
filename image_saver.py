import logging

import piexif
from PIL.ExifTags import TAGS
from PIL import Image

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

# TODO: Consider whether this really needs to be a class as it's a singleton

@singleton
class ImageSaver:
    def __init__(self):
        self.__directory = None

    def set_config(self, config):
        self._config = config

    def save_array(self, array, recording_time, motion_detected, algorithm_data):
        if motion_detected:
            file_name = f"{self._config['capture']['output_dir']}{recording_time:%Y-%m-%d %H%M%S}.{recording_time.microsecond // 1000:05d}-d.jpg"
        else:
            file_name = f"{self._config['capture']['output_dir']}{recording_time:%Y-%m-%d %H%M%S}.{recording_time.microsecond // 1000:05d}.jpg"

        image = Image.fromarray(array).convert("RGB")

        try:
            if self._config["capture"]["save_images"]:
                # This link was useful for this. I had trouble just using PILLOW. https://stackoverflow.com/a/63649983
                txt = f"1234578 Algorithm Data coming soon\n"
                exif_ifd = {piexif.ExifIFD.UserComment: txt.encode()}

                exif_dict = {"0th": {}, "Exif": exif_ifd, "1st": {},
                        "thumbnail": None, "GPS": {}}

                exif_dat = piexif.dump(exif_dict)
                image.save(file_name, exif=exif_dat)
        except Exception as e:
            logging.error(f"An error occurred saving the image: {e}")

    def save_image(self, image, recording_time, motion_detected, algorithm_data):
        if motion_detected:
            file_name = f"{self._config['capture']['output_dir']}{recording_time:%Y-%m-%d %H%M%S}.{recording_time.microsecond // 1000:05d}-d.jpg"
        else:
            file_name = f"{self._config['capture']['output_dir']}{recording_time:%Y-%m-%d %H%M%S}.{recording_time.microsecond // 1000:05d}.jpg"

        try:
            if self._config["capture"]["save_images"]:
                # This link was useful for this. I had trouble just using PILLOW. https://stackoverflow.com/a/63649983
                txt = f"1234578 {algorithm_data['hist_diff']:.0f}\n"
                exif_ifd = {piexif.ExifIFD.UserComment: txt.encode()}

                exif_dict = {"0th": {}, "Exif": exif_ifd, "1st": {},
                        "thumbnail": None, "GPS": {}}

                exif_dat = piexif.dump(exif_dict)
                image.save(file_name, exif=exif_dat)
        except Exception as e:
            logging.error(f"An error occurred saving the image: {e}")

    def save_intermediate_image(self, image, recording_time, algorithm_data):
        file_name = f"{self._config['capture']['output_dir']}{recording_time:%Y-%m-%d %H%M%S}.{recording_time.microsecond // 1000:05d}-2.jpg"

        try:
            image.save(file_name)
        except Exception as e:
            logging.error(f"An error occurred saving the image: {e}")

    def save_intermediate_images(self, current_image, previous_image, recording_time, algorithm_data):
        current_file_name = f"{self._config['capture']['output_dir']}{recording_time:%Y-%m-%d %H%M%S}.{recording_time.microsecond // 1000:05d}-2.jpg"
        previous_file_name = f"{self._config['capture']['output_dir']}{recording_time:%Y-%m-%d %H%M%S}.{recording_time.microsecond // 1000:05d}-1.jpg"

        try:
            # txt = f"1234578 {algorithm_data['hist_diff']:.0f}\n"
            txt = "1234579Data will go here\n"
            exif_ifd = {piexif.ExifIFD.UserComment: txt.encode()}

            exif_dict = {"0th": {}, "Exif": exif_ifd, "1st": {},
                    "thumbnail": None, "GPS": {}}

            exif_dat = piexif.dump(exif_dict)

            current_image.save(current_file_name, exif=exif_dat)
            previous_image.save(previous_file_name,  exif=exif_dat)

        except Exception as e:
            logging.error(f"An error occurred saving the image: {e}")
