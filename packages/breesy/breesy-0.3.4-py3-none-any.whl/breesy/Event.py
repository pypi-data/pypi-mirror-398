from .errors import BreesyError
from .type_hints import enforce_type_hints


class Event:
    """Represents an event in an EEG recording."""

    name: str
    """Name of the event"""

    index: int
    """Sample index where the event occurs"""

    def __str__(self):
        """Return a string representation of the Event object."""
        return self.__repr__()

    def __repr__(self):
        """Return a string representation of the Event object."""
        return f"Event(name='{self.name}', index={self.index})"

    def __lt__(self, event2):
        return self.index < event2.index

    @enforce_type_hints
    def __init__(self, name: str, index: int):
        """Initialize an Event.

        :param name: Name of the event
        :param index: Sample index where the event occurs
        """
        self.name = name

        if index < 0:
            raise BreesyError(
                f"Event index should be 0 or more, but got {index} instead.",
                "Make sure that the event index is a non-negative integer. E.g.: 0 or 1000. "
                "For instance, an event index of 1000 at 512 Hz sample rate corresponds to ~2 seconds into the recording."
            )
        self.index = index
