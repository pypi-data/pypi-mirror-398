import os
from logging.handlers import BaseRotatingHandler


class ManualRotatingFileHandler(BaseRotatingHandler):
    """
    Custom RotatingFileHandler that allows manual rotation of log files.
    """

    def __init__(
        self,
        filepath,
        key: str = "msg",
        mode: str = "a",
        encoding=None,
    ):
        """
        Initialize the handler with the given filename and mode.
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        super().__init__(filepath, delay=True, mode=mode, encoding=encoding)
        self.current_filepath = None
        self.next_filepath = None
        self.key = key

    def shouldRollover(self, record):
        """
        Determine if a rollover should occur,
        which is whenever a Header record is logged with a new filepath
        """
        assert hasattr(record, self.key), f"Record must have the key '{self.key}'"
        record_obj = getattr(record, self.key)
        if hasattr(record_obj, "filepath"):
            new_filepath = getattr(record_obj, "filepath")
            if new_filepath != self.current_filepath:
                # Rollover condition met
                if self.current_filepath is None:
                    # This is the first header file,
                    # set the current filepath to the first header's filepath
                    self.current_filepath = new_filepath
                else:
                    assert (
                        self.next_filepath is None
                    ), "Next filepath should be None due to previous rollover."
                    self.next_filepath = new_filepath
        assert (
            self.current_filepath is not None
        ), "Current filepath should not be None. First message should always be a Header."
        return self.next_filepath is not None

    def doRollover(self):
        """
        Perform the rollover by closing the current stream and renaming the file.
        """
        assert self.current_filepath is not None, "Current filepath should not be None."
        os.makedirs(os.path.dirname(self.current_filepath), exist_ok=True)
        if self.stream:
            self.stream.close()
            self.stream = None  # type: ignore[assignment]
        self.rotate(self.baseFilename, self.current_filepath)
        self.current_filepath = self.next_filepath
        self.next_filepath = None
        if not self.delay:
            self.stream = self._open()

    def close(self):
        assert (
            self.next_filepath is None
        ), "Next filepath should be None before closing."
        if self.current_filepath is not None:
            # Ensure we perform a rollover if there is a current filepath
            # before closing the handler
            self.doRollover()
        super().close()
