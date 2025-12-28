# -*- coding: utf-8 -*-
import time

from .enums import StateKey

class State:
    def __init__(self):
        self._data = {}

    def set(self, key: str, value) -> None:
        self._data[key] = value

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def has(self, key: str):
        return key in self._data

    def append(self, key: str, value):
        self._data.setdefault(key, []).append(value)

    def timer_start(self, timer_key: str):
        self._data.setdefault(StateKey.TIME_DURATION.value, {})[timer_key] = time.time() * 1000

    def timer_end(self, timer_key: str) -> bool:
        timer_data = self._data.get(StateKey.TIME_DURATION.value, {})
        if timer_key in timer_data:
            timer_data[timer_key] = round(time.time() * 1000 - timer_data[timer_key], 2)
            return True
        return False

    def time_cost(self, timer_key) -> float:
        return round(self._data.get(StateKey.TIME_DURATION.value, {}).get(timer_key, 0), 2)

    def to_dict(self) -> dict:
        return {
            "data": self._data.copy()
        }

    def from_dict(self, data: dict) -> None:
        if data:
            self._data.update(data.get("data", {}))