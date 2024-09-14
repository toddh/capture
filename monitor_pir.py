
import threading
import gpiod
import time

class MonitorPIR(threading.Thread):

    def __init__(self, config):
        super(MonitorPIR, self).__init__()
        self._stop_event = threading.Event()
        self._config = config

        if self._config["pir"]["check_pir"]:
            self._chip = gpiod.Chip('gpiochip4')
            self._line = self._chip.get_line(self._config["pir"]["line"])
            self._line.request(consumer='button', type=gpiod.LINE_REQ_DIR_IN)

        self.__pir_detected = False

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def _poll_pir(self, config):
        while not self._stop_event.is_set():

            if self._config["pir"]["check_pir"]:
                value = self._line.get_value()
                
                if value == 0:
                    self.__pir_detected = False
                else:
                    self.__pir_detected = True

            time.sleep(self._config["pir"]["dwell"])


        if self._config["pir"]["check_pir"]:
            self._line.release()
            self._chip.close()

    def pir_detected(self):
        return self.__pir_detected

    def start(self):
        thread = threading.Thread(target=MonitorPIR._poll_pir, args=(self, self._config))
        thread.daemon = True
        thread.start()

