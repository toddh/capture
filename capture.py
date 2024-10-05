#!/usr/bin/python3
import argparse
import logging
import signal
import sys

import tomllib
from picamera2 import Picamera2
import stats_file
import monitor_pir
from image_capture_loop import ImageCaptureLoop
from image_saver import ImageSaver


Picamera2.set_logging(logging.ERROR)
pir_thread = None

def command_line_handler(signum, frame):
    # res = input("Ctrl-c was pressed. Do you really want to exit? y/n ")
    res = "y"
    if res == "y":
        logging.info("stopping")
        stop()

def load_config():
    try:
        with open("config.toml", "rb") as f:
            config = tomllib.load(f)
    except Exception as e:
        logging.critical(f"An error occurred while configuring: {e}")
        sys.exit(1)

    # Override the configuration with command line arguments

    parser = argparse.ArgumentParser(
        prog="Capture", description="Detect motion and capture images."
    )

    parser.add_argument("-p", "--preview", action="store_true", help="Enable preview")
    parser.add_argument("-r", "--rectangles", action="store_true", help="Draw rectangles on the image")
    parser.add_argument("-pp", "--opencv_preview", action="store_true")
    parser.add_argument('--flip', action=argparse.BooleanOptionalAction)
    parser.add_argument("-l", "--logging", type=str, help="Set logging level", default="ERROR")

    args = parser.parse_args()

    if args.preview:
        config["preview"]["enable"] = True



    if args.flip is None:
        pass
    elif args.flip:
        config["capture"]["flip"] = True
    else:
        config["capture"]["flip"] = False


    # Model specific overrides
    if args.opencv_preview:
        config["opencv"]["preview"] = True
    if args.rectangles:
        config["tflite"]["draw_rectangles"] = True

    logger = logging.getLogger()
    logger.setLevel(args.logging)

    return config
    
def stop():
    # stop_event.set()  # Signal the thread to stop
    # thread.join()
    if config['pir']['check_pir']:
        pir_thread.stop()
    sys.exit(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    config = load_config()

    if config['pir']['check_pir']:
        pir_thread = monitor_pir.MonitorPIR(config)
        pir_thread.start()

    image_capture_loop = ImageCaptureLoop(config, pir_thread)

    image_saver = ImageSaver()
    image_saver.set_config(config)

    stats_file.start_stats_thread(config)

    signal.signal(signal.SIGINT, command_line_handler)
    image_capture_loop.start()
