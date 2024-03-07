from utils.paths import Path
import json


__all__ = (
    "selection",
)


class Selection:
    def __init__(self):
        with open(Path.to_saved_data(), mode='r') as file:
            self.data: dict = json.load(file)

    def save(self):
        with open(Path.to_saved_data(), mode='w') as file:
            json.dump(self.data, file)

    def update(self, window: str, slot: str, value):
        self.data[window][slot] = value

    def get(self, window: str, slot: str, default):
        try:
            res = self.data.get(window).get(slot)
            if res is None:
                return default
            else:
                return res
        except AttributeError:
            return default


selection = Selection()
