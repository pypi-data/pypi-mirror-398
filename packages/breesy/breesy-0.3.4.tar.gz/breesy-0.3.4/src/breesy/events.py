import numpy as np

from breesy.type_hints import enforce_type_hints
from breesy.logging import logger


@enforce_type_hints
def get_simple_windows(data: np.ndarray, sample_rate: int | float, window_length: int | float) -> np.ndarray:
    """Split EEG data into non-overlapping windows of specified duration.

    :param data: EEG data array of shape (channels, samples)
    :param sample_rate: Sampling rate in Hz
    :param window_length: Duration of each window in seconds

    :return: 3D array of shape (n_windows, n_channels, samples_per_window)
    """

    # these windows won't have overlap
    # returns 3D array where 1st dimension is windows, then channel and time
    # window length should be in seconds
    if (window_length_in_samples_float := window_length * sample_rate) != round(window_length_in_samples_float):
        logger.warning("There will be window length rounding error")
    window_length_in_samples = int(round(window_length_in_samples_float))

    splitting_indices = np.arange(0, data.shape[-1], window_length_in_samples)[1:]
    windows = np.array_split(data, splitting_indices, axis=-1)
    if windows[-1].shape[-1] < window_length_in_samples:  # last window is shorter than needed
        return np.array(windows[:-1])
        # also print out a warning/message that the last piece was discarded
        # also add an option to cut it differently so the shorter piece is at the start
    return np.array(windows)

@enforce_type_hints
def get_overlapping_windows(data: np.ndarray, sample_rate: int | float, window_length: int | float,
                            window_overlap: float) -> np.ndarray:
    """Split EEG data into overlapping windows of specified duration.

    :param data: EEG data array of shape (channels, samples)
    :param sample_rate: Sampling rate in Hz
    :param window_length: Duration of each window in seconds
    :param window_overlap: Duration of overlap between consecutive windows in seconds

    :return: 3D array of shape (n_windows, n_channels, samples_per_window)
    """

    if (window_length_in_samples_float := window_length * sample_rate) != round(window_length_in_samples_float):
        logger.warning("There will be window length rounding error")
    window_length_in_samples = int(round(window_length_in_samples_float))

    if (window_overlap_in_samples_float := window_overlap * sample_rate) != round(window_overlap_in_samples_float):
        logger.warning("There will be window overlap rounding error")  # TODO: nicer messages
    window_overlap_in_samples = int(round(window_overlap_in_samples_float))

    slide = window_length_in_samples - window_overlap_in_samples

    windows = np.lib.stride_tricks.sliding_window_view(
        data,
        window_shape=(data.shape[0], window_length_in_samples),
        axis=(0, 1))[0, ::slide]
    return windows


if __name__ == "__main__":
    data = np.random.randn(2, 1000)
    sample_rate = 250
    window_length = 1.0
    window_overlap = 0.5

    simple_windows = get_simple_windows(data, sample_rate, window_length)
    print(simple_windows.shape)

    overlapping_windows = get_overlapping_windows(data, sample_rate, window_length, window_overlap)
    print(overlapping_windows.shape)


