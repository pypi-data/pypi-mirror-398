import logging
import threading
from importlib.util import module_from_spec, spec_from_file_location


class ClassFactory:
    _lock = threading.Lock()
    _inst = None

    def __init__(self):
        self._classes = {}

    def load(self, name: str, path: str, class_name: str):
        if name in self._classes:
            return True

        spec = spec_from_file_location(name, path)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)

        c = getattr(module, class_name, None)
        if c is None:
            logging.error(f"class not found: {path}:{class_name}")
            return False

        self._classes[name] = c
        return True

    def get(self, name: str):
        if name in self._classes:
            return self._classes[name]()

        logging.error(f"get class faied, class not found {name}")
        return None
