import logging


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

    def set_config(self, config):
        self._config = config

    def save_image(self, image, recording_time, motion_detected, algorithm_data):
        if motion_detected:
            file_name = f"{self._config['capture']['output_dir']}{recording_time:%Y-%m-%d %H%M%S}.{recording_time.microsecond // 1000:03d}-d.jpg"
        else:
            file_name = f"{self._config['capture']['output_dir']}{recording_time:%Y-%m-%d %H%M%S}.{recording_time.microsecond // 1000:03d}.jpg"

        # TODO: Save the Meta Data somehow.  Maybe in exif?

        try:
            if self._config["capture"]["save_images"]:
                image.save(file_name)
            # TODO: Decide whether to do image.save or picam2.capture_file
        except Exception as e:
            logging.error(f"An error occurred saving the detection image: {e}")
