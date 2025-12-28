from .enums import Status


class CortexException(Exception):
    def __init__(self, status=Status.RUN_TIME_ERROR, message=None):
        self.status: Status = status
        self.message = message

        if self.message is None:
            self.message = self.status.name

        super().__init__(self.message)
