import logging
from abc import ABC, abstractmethod
from typing import Callable

import yaml

from .context import Context
from .state import State


class Processor(ABC):
    trigger: Callable[[list], bool]
    stop: Callable[[str], bool]

    def __init__(self, name: str = ""):
        self.name = name
        self.class_name = ""
        self.cortex = ""
        self.group = ""
        self.events = []
        self.conditions = {}
        self.reentrant = False
        self.in_degree = 0
        self.config = {}

    def init(self) -> bool:
        return True

    @abstractmethod
    async def process(self, ctx: Context, state: State) -> bool:
        raise NotImplementedError("process method is not implemented error!")

    @property
    def is_required(self):
        return self.config.get("required", False)

    def increment_in_degree(self):
        self.in_degree += 1


def node(config: str = ""):
    def decorator(c):
        init_original = c.init

        def init_proxy(self):
            if config:
                try:
                    with open(config, "r") as f:
                        self.config = yaml.load(f, Loader=yaml.FullLoader)
                except Exception as e:
                    logging.error(f"failed to read config file: {config}, error: {e}")
                    return False

            init_original(self)

        c.init = init_proxy
        return c

    return decorator
