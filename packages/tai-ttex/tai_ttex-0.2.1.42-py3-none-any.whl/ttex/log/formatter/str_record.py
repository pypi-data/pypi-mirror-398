from abc import ABC, abstractmethod


class StrRecord(ABC):
    """
    Abstract base class for a record in a file.
    This class defines the structure and methods that all record types must implement.
    """

    @abstractmethod
    def __str__(self) -> str:
        """
        Abstract method to format the record as a string.
        Must be implemented by subclasses.

        Returns:
            str: Formatted record string.
        """
        pass

    def emit(self) -> bool:
        return True


class StrHeader(StrRecord):
    """
    Abstract base class for a header in a file.
    This class extends Record and defines the structure and methods that all header types must implement.
    """

    @property
    @abstractmethod
    def uuid(self) -> str:
        """
        Abstract property to get the UUID of the header.
        Must be implemented by subclasses.
        Decides if summary statistics are reset

        Returns:
            str: The UUID of the header.
        """
        pass

    @property
    @abstractmethod
    def filepath(self) -> str:
        pass
