from logging import Filter


class KeyFilter(Filter):
    """
    Filter to allow only log records with a specific key and unique UUID.
    If a record with the same UUID as the last one is encountered, it will be filtered
    out to avoid duplicate logging.
    """

    def __init__(self, key: str, name: str = "KeyFilter"):
        """
        Initialize the COCOHandlerFilter with an optional name.
        """
        self.key = key
        self.uuid = None
        super().__init__(name)

    def filter(self, record):
        """ """
        if not hasattr(record, self.key):
            return False

        key_record = getattr(record, self.key, None)
        assert key_record is not None
        if hasattr(key_record, "uuid"):
            if key_record.uuid == self.uuid:
                # If the UUID is the same, do not log this record
                return False
            self.uuid = key_record.uuid
            return True
        return True
