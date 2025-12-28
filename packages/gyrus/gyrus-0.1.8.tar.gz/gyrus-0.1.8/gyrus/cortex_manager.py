import yaml

from .cortex import Cortex


class CortexManager:
    def __init__(self, config):
        self._cortices = {}

        for item in config:
            with open(item["path"], "r") as f:
                instance = Cortex()
                instance.build(item["name"], yaml.safe_load(f))

                self._cortices[item["name"]] = instance

    def get(self, name):
        return self._cortices.get(name, None)
