import datetime
import logging
import time


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
        self.__num_images = None

    def set_defaults(self, directory, num_images, picam2):
        self.__directory = directory
        self.__num_images = num_images
        self.__picam2 = picam2

    def save_detection_image(self, image, diff):
        recording_time = datetime.datetime.now()
        file_name = f"{self.__directory}{recording_time:%Y-%m-%d %H%M%S}.{recording_time.microsecond // 1000:03d}-{diff:04.0f}-d.jpg"
        try:
            image.save(file_name)
        except Exception as e:
            logging.error(f"An error occurred saving the detection image: {e}")

    def capture(self, triggered, diff):

        if triggered:
            for _ in range(self.__num_images):
                file_path = self.get_capture_file_name(triggered, diff)
                # logging.info(f"Capturing to file {file_path}")
                try:
                    self.__picam2.capture_file(file_path)
                except Exception as e:
                    logging.error(f"An error occurred capturing to the file: {e}")

                time.sleep(1)
        else:
            file_path = self.get_capture_file_name(triggered, diff)
            # logging.info(f"Capturing to file {file_path}")
            try:
                self.__picam2.capture_file(file_path)
            except Exception as e:
                logging.error(f"An error occurred capturing to the file: {e}")            

    def get_capture_file_name(self, triggered, diff):
        recording_time = datetime.datetime.now()
        if (triggered):
            file_name = f"{self.__directory}{recording_time:%Y-%m-%d %H%M%S}.{recording_time.microsecond // 1000:03d}-{diff:04.0f}-t.jpg"
        else:
            file_name = f"{self.__directory}{recording_time:%Y-%m-%d %H%M%S}.{recording_time.microsecond // 1000:03d}-{diff:04.0f}.jpg"
        return file_name
