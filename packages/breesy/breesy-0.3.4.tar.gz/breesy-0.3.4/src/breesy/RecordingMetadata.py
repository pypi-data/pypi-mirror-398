from pathlib import Path

from .type_hints import enforce_type_hints


class RecordingMetadata:
    """Metadata for an EEG recording."""

    name: str
    """Name of the recording"""

    file_path: Path
    """Path to the source file"""

    description: str
    """Optional description of the recording"""

    def __str__(self):
        """Return a string representation of the RecordingMetadata object."""
        return self.__repr__()

    def __repr__(self):
        """Return a string representation of the RecordingMetadata object."""
        description_repr = f", description='{self.description}'" if self.description else ""
        return f"RecordingMetadata(name='{self.name}', file_path='{self.file_path}'{description_repr})"

    @enforce_type_hints
    def __init__(self, name: str, file_path: Path, description: str | None = None):
        """Initialize RecordingMetadata.

        :param name: Name of the recording
        :param file_path: Path to the source file
        :param description: Optional description of the recording
        """
        self.name = name
        self.file_path = file_path
        self.description = description
