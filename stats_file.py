
import datetime
import logging
import threading
import time

from gpiozero import CPUTemperature

import running_average

stats_file = None
last_timestamp = datetime.datetime.now()
num_samples = 0
ra = running_average.RunningAverage()
average_time = 0
average_diff = 0


class StoppableThread(threading.Thread):
    """Class to create a thread that can be stopped."""

    def __init__(self, *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


def accumulate_stats(timestamp, diff):
    global last_timestamp, average_time, average_diff

    average_time = ra.update((timestamp - last_timestamp).total_seconds())
    last_timestamp = last_timestamp

    average_diff = ra.update(diff)

def output_stats(stats_file_name, interval):
    """Writes CPU temperature to the stats file every hour until stop_event is set."""
    global stats_file

    while True:
        recording_time = datetime.datetime.now()
        cpu = CPUTemperature()
        stats_file.write(f"{recording_time:%Y-%m-%d %H:%M:%S} cpu_temp: {cpu.temperature} avg_time: {average_time} avg_diff: {average_diff}\n")
        stats_file.close()
        time.sleep(interval)

def open_stat_file(stats_file_name):
    global stats_file

    try:
        stats_file = open(stats_file_name, "a+")
        stats_file.write("CPU temperature\n")
        return stats_file
    except IOError as e:
        logging.error(f"Error opening file {stats_file_name}: {e}")
        return None

def start_stats_thread(config):
    global stats_file


    recording_time = datetime.datetime.now()
    stats_file_name = (
        f"{config['capture']['output_dir']}/stats-{recording_time:%Y-%m-%d %H%M%S}.txt")

    stats_file = open_stat_file(stats_file_name)

    stop_event = threading.Event()
    thread = StoppableThread(target=output_stats, args=(stop_event))

    # Start the statics thread

    thread = threading.Thread(target=output_stats, args=(stats_file_name, config['stats']['interval']))
    thread.daemon = True
    thread.start()
