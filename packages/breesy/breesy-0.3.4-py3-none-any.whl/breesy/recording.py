import numpy as np

from .Event import Event
from .RecordingMetadata import RecordingMetadata
from .errors import BreesyError
from .type_hints import enforce_type_hints
from .logging import logger


class Recording:
    """Represents an EEG recording with data, channel information, and events."""

    data: np.ndarray
    """EEG data array of shape (channels, samples)"""

    channel_names: list[str]
    """List of channel names"""

    sample_rate: int | float
    """Sampling rate in Hz"""

    events: list[Event] | None
    """List of Event objects"""

    metadata: RecordingMetadata | None
    """Additional metadata about the recording"""

    @enforce_type_hints
    def __init__(self,
                 data: np.ndarray,
                 channel_names: list[str],
                 sample_rate: int | float,
                 events: list[Event] | None = None,
                 metadata: RecordingMetadata | None = None, ):
        """Initialize a Recording.

        :param data: EEG data array of shape (channels, samples)
        :param channel_names: List of channel names
        :param sample_rate: Sampling rate in Hz
        :param events: List of Event objects
        :param metadata: Additional metadata about the recording
        """

        if data.ndim != 2:
            raise BreesyError(
                "The EEG data provided has an incorrect number of dimensions. Expected data.ndim to be 2, but got "
                f"{data.ndim} dimensions instead.",
                "The data provided is likely not EEG data, or there are several records joined into one file. However, Breesy only supports ordinary two-dimensional EEG data for now."
            )

        n_channels, n_samples = data.shape
        if (n_channels != len(channel_names)) and (n_samples != len(channel_names)):
            raise BreesyError(
                f"The number of channel names ({len(channel_names)}) provided does not match the "
                f"number of channels ({n_channels}) in the EEG data.",
                "Make sure that the number of channel names provided matches the number of channels in the EEG data."
                "You can see the number of channel names like this: len(eeg_channel_names)."
            )
        elif (n_channels != len(channel_names)) and (n_samples == len(channel_names)):
            logger.warning('data rows and columns will be switched places according to the provided channel names.')
            self.data = data.T
        else:
            self.data = data

        self.channel_names = channel_names

        if sample_rate <= 0:
            raise BreesyError(
                f"Sample rate should be more than 0, but you provided {sample_rate}.",
                "Make sure that the sample rate is a positive integer. E.g., a sample rate of: 512."
            )

        is_typical_sample_rate = 100 < sample_rate < 5000
        if not is_typical_sample_rate:
            logger.warning(f"Unusual sample rate ({sample_rate} Hz). Typical EEG sample rates range from 128-2000 Hz.")
        self.sample_rate = sample_rate

        if events is None:
            events = []
        self._set_events(events)

        self.metadata = metadata

    def _set_events(self, events: list[Event]) -> None:
        out_of_range_events = [event for event in events if event.index >= self.number_of_samples]
        if out_of_range_events:
            raise BreesyError(
                f"Found {len(out_of_range_events)} events with indices out of range for the provided EEG data. "
                f"First Got index {out_of_range_events[0].index} while the EEG data has {self.number_of_samples} samples.",
                "Make sure that the event indices are within the range of the EEG data. "
                "For instance, if the EEG data has 10000 samples, the event indices should be less than 10000. "
                "You can see the number of samples in the EEG data like so: eeg_data.shape[1]."
            )

        sorted_events = sorted(events, key=lambda event: event.index)
        self.events = sorted_events

    def __repr__(self):
        """Return a string representation of the Recording object."""
        metadata_repr = f", name={self.metadata.name}" if self.metadata else ""
        events_repr = f", event_count={len(self.events)}" if self.events else ""
        return (f"Recording("
                f"channels={self.number_of_channels}, "
                f"duration={self.duration:.2f} s, "
                f"sample_rate={self.sample_rate} Hz"
                f"{metadata_repr}"
                f"{events_repr}"
                f")")


    @property
    def number_of_channels(self):
        """Return the number of channels in the recording."""
        return self.data.shape[0]

    @property
    def duration(self):
        """Return the duration of the recording in seconds."""
        return self.data.shape[1] / self.sample_rate

    @property
    def number_of_samples(self):
        """Return the number of samples in the recording."""
        return self.data.shape[1]


@enforce_type_hints
def cut_by_sample_range(recording: Recording, start_index: int, end_index: int) -> Recording:
    """Cut a recording to a specific sample range.

    :param recording: Input recording
    :param start_index: Start sample index
    :param end_index: End sample index

    :return: New recording containing only the specified sample range
    """
    if start_index < 0 or end_index > recording.number_of_samples:
        raise BreesyError(
            f"Requested to cut from {start_index} to {end_index}, but the recording has only {recording.number_of_samples} samples.",
            "Make sure that the start and end sample indices are within the range of the recording samples. "
            "You can see the number of samples in the recording like so: recording.number_of_samples."
        )

    # Take both ends inclusive so that the events themselves also fit in the epoch
    new_eeg_data = recording.data[:, start_index:end_index + 1]
    events_in_new_data = [event for event in (recording.events or []) if start_index <= event.index <= end_index]
    events_with_offset = [Event(e.name, e.index - start_index) for e in events_in_new_data]

    return Recording(
        data=new_eeg_data,
        channel_names=recording.channel_names,
        sample_rate=recording.sample_rate,
        events=events_with_offset,
        metadata=recording.metadata
    )


@enforce_type_hints
def cut_by_second_range(recording: Recording, start_second: float | int, end_second: float | int):
    """Cut a recording to a specific time range.

    :param recording: Input recording
    :param start_second: Start time in seconds
    :param end_second: End time in seconds

    :return: New recording containing only the specified time range
    """
    if start_second > end_second:
        raise BreesyError(
            f"Requested to cut from {start_second} s to {end_second} s, but the start time is higher than the end time.",
            "Make sure that the start time is lower than the end time."
        )

    if end_second > recording.duration:
        raise BreesyError(
            f"Requested to cut from {start_second} s to {end_second} s, but the recording has only {recording.duration}s.",
            "Make sure that the start and end seconds are within the range of the recording duration. "
            "You can see the recording duration like so: recording.duration."
        )

    start_index = int(recording.sample_rate * start_second)
    end_index = int(recording.sample_rate * end_second)

    return cut_by_sample_range(recording, start_index, end_index)


@enforce_type_hints
def add_events(recording: Recording, events: list[Event]) -> Recording:
    """Create a new recording with additional events.

    :param recording: Input recording
    :param events: List of events to add

    :return: New recording with added events
    """
    new_events = recording.events or [] + events
    return Recording(
        data=recording.data,
        channel_names=recording.channel_names,
        sample_rate=recording.sample_rate,
        events=new_events,
        metadata=recording.metadata
    )


@enforce_type_hints
def remove_channels(recording: Recording, channels_to_remove: list[str]) -> Recording:
    """Create a new recording with specified channels removed.

    :param recording: Input recording
    :param channels_to_remove: List of channel names to remove

    :return: New recording without the specified channels
    """
    missing_channels = [channel for channel in channels_to_remove if channel not in recording.channel_names]
    if missing_channels:
        raise BreesyError(
            f"Channels to remove contain channel names that are not present in the recording, namely: {missing_channels}.",
            "Make sure that the channel names provided to remove are present in the recording. "
            "Double check that you haven't removed those channels for this data already. "
            "You can see the channel names in the recording with: recording.channel_names."
        )

    channel_indices_to_remove = [recording.channel_names.index(channel) for channel in channels_to_remove]
    new_eeg_data = np.delete(recording.data, channel_indices_to_remove, axis=0)
    new_channel_names = [channel for channel in recording.channel_names if channel not in channels_to_remove]
    return Recording(
        data=new_eeg_data,
        channel_names=new_channel_names,
        sample_rate=recording.sample_rate,
        events=recording.events,
        metadata=recording.metadata
    )


@enforce_type_hints
def select_channels(recording: Recording, channels_to_select: list[str]) -> Recording:
    """Create a new recording with only the specified channels.

    :param recording: Input recording
    :param channels_to_select: List of channel names to keep

    :return: New recording with only the specified channels
    """
    missing_channels = [channel for channel in channels_to_select if channel not in recording.channel_names]
    if missing_channels:
        raise BreesyError(
            f"Channels to select contain channel names that are not present in the recording, namely: {missing_channels}.",
            "Make sure that the channel names provided to select are present in the recording. "
            "You can see the channel names in the recording with: recording.channel_names."
        )

    channel_indices_to_select = [recording.channel_names.index(channel) for channel in channels_to_select]
    new_eeg_data = recording.data[channel_indices_to_select]
    return Recording(
        data=new_eeg_data,
        channel_names=channels_to_select,
        sample_rate=recording.sample_rate,
        events=recording.events,
        metadata=recording.metadata
    )


@enforce_type_hints
def set_channel_names(recording: Recording, ch_names: list[str]) -> Recording:
    """Set new channel names for a recording.

    :param recording: Input recording
    :param ch_names: List of new channel names

    :return: New recording with updated channel names
    """
    if len(ch_names) != recording.number_of_channels:
        raise BreesyError(
            f"{len(ch_names)} channel names are provided, but data has {recording.number_of_channels} channels. "
            "Please recheck your list of channel names. "
        )
    return Recording(
        data=recording.data,
        channel_names=ch_names,
        sample_rate=recording.sample_rate,
        events=recording.events,
        metadata=recording.metadata
    )


@enforce_type_hints
def get_events_by_name(recording: Recording, event_name: str) -> list[Event]:
    """Return a list of events with a specific name.

    :param recording: Input recording
    :param event_name: Name of events to find

    :return: List of events with the specified name
    """
    return [event for event in recording.events if event.name == event_name]


@enforce_type_hints
def split_by_continuous_events(recording: Recording, start_event_name: str, end_event_name: str) -> list[Recording]:
    """Split a recording into segments between start and end events.

    :param recording: Input recording
    :param start_event_name: Name of events marking segment starts
    :param end_event_name: Name of events marking segment ends

    :return: List of recording segments between each start-end event pair
    """
    if not recording.events:
        raise BreesyError(
            "No events found in the recording.",
            "Make sure that the recording has events. You can see the number of events like so: len(recording.events)."
        )

    start_events = get_events_by_name(recording, start_event_name)
    end_events = get_events_by_name(recording, end_event_name)

    if len(start_events) != len(end_events):
        raise BreesyError(
            f"Found {len(start_events)} start events and {len(end_events)} end events. "
            "Expected the number of start and end events to be the same.",
            "Make sure each start event has a corresponding end event. "
            "You can see the number of start events like so: get_events_by_name(recording, start_event_name); "
            "number of end events: get_events_by_name(recording, end_event_name)."
        )

    epoch_recordings = []
    for start_event, end_event in zip(start_events, end_events):
        if start_event.index >= end_event.index:
            pair_number = start_events.index(start_event) + 1
            raise BreesyError(
                f"When going pairwise through events, found a pair (nr. {pair_number}) where start event index ({start_event.index}) is higher than the end event index ({end_event.index}).",
                "Inspect the events manually, for start events: get_events_by_name(recording, start_event_name); "
                "end events: get_events_by_name(recording, end_event_name). "
                "Make sure that the start event index is lower than the end event index. "
            )

        epoch_recording = cut_by_sample_range(recording, start_event.index, end_event.index)
        epoch_recordings.append(epoch_recording)

    return epoch_recordings


@enforce_type_hints
def split_by_events(recording: Recording, event_name: str, duration: float | int = 5.0) -> list[Recording]:
    """Split a recording into segments starting at specified events.

    :param recording: Input recording
    :param event_name: Name of events to use as segment starts
    :param duration: Duration of each segment in seconds

    :return: List of recording segments starting at each event
    """
    events = get_events_by_name(recording, event_name)

    epoch_recordings = []
    for event in events:
        end_index = int(event.index + recording.sample_rate * duration)
        epoch_recording = cut_by_sample_range(recording, event.index, end_index)
        epoch_recordings.append(epoch_recording)

    return epoch_recordings


@enforce_type_hints
def split_by_window_duration(recording: Recording, window_duration: float | int, overlap_duration: float | int = 0.0) -> list[Recording]:
    """Split a recording into equal-sized segments of specified duration with optional overlap.

    :param recording: Input recording
    :param window_duration: Duration of each segment in seconds
    :param overlap_duration: Duration of overlap between consecutive segments in seconds (default: 0.0)

    :return: List of equal-sized recording segments
    """
    if overlap_duration < 0:
        raise BreesyError(
            f"Overlap duration ({overlap_duration}s) cannot be negative.",
            "Provide a non-negative overlap duration value."
        )

    if overlap_duration >= window_duration:
        raise BreesyError(
            f"Overlap duration ({overlap_duration}s) must be less than window duration ({window_duration}s).",
            "Provide an overlap duration that is smaller than the window duration."
        )

    num_samples_per_epoch = int(window_duration * recording.sample_rate)

    if num_samples_per_epoch > recording.number_of_samples:
        raise BreesyError(
            f"Epoch duration ({window_duration}s) is longer than the recording duration ({recording.duration}s).",
            "Make sure that the epoch duration is shorter than the recording duration. "
            "You can see the recording duration like so: recording.duration."
        )

    step_duration = window_duration - overlap_duration
    step_samples = int(step_duration * recording.sample_rate)

    max_start_sample = recording.number_of_samples - num_samples_per_epoch
    num_epochs = (max_start_sample // step_samples) + 1

    epoch_recordings = []
    for i in range(num_epochs):
        start_index = i * step_samples
        end_index = start_index + num_samples_per_epoch

        # skip window if out of bounds
        if end_index > recording.number_of_samples:
            break

        epoch_data = recording.data[:, start_index:end_index]
        epoch_recording = Recording(
            data=epoch_data,
            channel_names=recording.channel_names,
            sample_rate=recording.sample_rate,
            events=recording.events,
            metadata=recording.metadata
        )
        epoch_recordings.append(epoch_recording)

    return epoch_recordings


@enforce_type_hints
def update_data(recording: Recording, new_eeg_data: np.ndarray) -> Recording:
    """Create a new recording with updated EEG data.

    :param recording: Input recording
    :param new_eeg_data: New EEG data array to use

    :return: New recording with updated data but same metadata and events
    """
    if recording.number_of_samples != new_eeg_data.shape[1]:
        raise BreesyError(
            f"New EEG data has a different number of samples ({new_eeg_data.shape[1]}) than the original EEG data ({recording.number_of_samples}).",
            "Make sure that the new EEG data has the same number of samples as the original EEG data. "
            "You can see the number of samples in the original EEG data like so: recording.number_of_samples."
        )

    return Recording(
        data=new_eeg_data,
        channel_names=recording.channel_names,
        sample_rate=recording.sample_rate,
        events=recording.events,
        metadata=recording.metadata
    )
