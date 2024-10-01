import cv2

from image_saver import ImageSaver


# Useful reference https://blog.teclado.com/python-abc-abstract-base-classes/

class AbstractObjectDetector:
    def __init__(self, config):
        self._config = config
        self._image_saver = ImageSaver()
        self._image_saver.set_config(config)


