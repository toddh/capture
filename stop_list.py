
class StopList:

    def __init__(self) -> None:

        self.stop_list = None

    def set_stop_list(self, stop_list: list) -> None:

        self.stop_list = stop_list

    def is_in_stop_list(self, word: str) -> bool:
        return word in self.stop_list
