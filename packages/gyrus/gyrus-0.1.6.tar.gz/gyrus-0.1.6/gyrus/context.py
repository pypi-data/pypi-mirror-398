from .enums import Status
from .stream import Stream


class Context:
    def __init__(self, parent: str = "root"):
        self._attributes = {
            "parent": parent,
            "stream": Stream(maxsize=10),
        }

    def __getattr__(self, name):
        if name in self._attributes:
            return self._attributes[name]

        if name == "status":
            return Status.SUCCESS

        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    def __setattr__(self, name, value):
        if name == "_attributes":
            super().__setattr__(name, value)
        else:
            self._attributes[name] = value

    def __delattr__(self, name):
        if name in self._attributes:
            del self._attributes[name]
        else:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._attributes["stream"].close()
        self._attributes.clear()

        return False

    def set(self, name, value):
        self._attributes[name] = value

    def get(self, name):
        return self._attributes.get(name)

    def clone(self, parent):
        ctx = Context(parent=parent)
        ctx.stream = self.stream

        for name, value in self._attributes.items():
            if name not in ["parent", "stream"]:
                ctx.set(name, value)

        return ctx
