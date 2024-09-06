
import datetime
import logging
import time

from gpiozero import CPUTemperature


def output_stats(stats_file_name, interval):
    """Writes CPU temperature to the stats file every hour until stop_event is set."""

    while True:
        stats_file = open_stat_file(stats_file_name)
        recording_time = datetime.datetime.now()
        cpu = CPUTemperature()
        stats_file.write(f"{recording_time:%Y-%m-%d %H:%M:%S} {cpu.temperature}\n")
        stats_file.close()
        time.sleep(interval)

def open_stat_file(stats_file_name):
    try:
        stats_file = open(stats_file_name, "a+")
        stats_file.write("CPU temperature\n")
        return stats_file
    except IOError as e:
        logging.error(f"Error opening file {stats_file_name}: {e}")
        return None

def start_stats_thread(stats_file_name, config):
    stats_file = open_stat_file(config["capture"]["dir"])
    stop_event = threading.Event()
    thread = StoppableThread(target=output_stats, args=(stop_event, config["capture"]["dir"]))

    Start the statics thread

    thread = threading.Thread(target=output_stats, args=(stats_file_name, config['stats']['interval']))
    thread.daemon = True
    thread.start()