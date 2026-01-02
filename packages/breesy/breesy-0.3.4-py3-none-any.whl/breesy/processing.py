from collections.abc import Callable
import numpy as np

from . import breesy_scipy, constants
from .recording import Recording, update_data
from .filtering import notch_filter
from .breesy_scipy import _si_periodogram, _si_welch
from .breesy_sklearn import _sklearn_fastica
from .errors import BreesyError, BreesyInternalError, protect_from_lib_error
from .type_hints import enforce_type_hints
from .logging import logger


@enforce_type_hints
def get_frequency_spectrum(recording: Recording, method: str = 'periodogram', scaling: str = 'density',
                           window: str | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Compute the frequency spectrum of EEG data using periodogram (default) or Welch method.

    :param recording: Input EEG recording
    :param method: Method to use to get frequency spectrum
    :param scaling: Scaling to use, either "density" (default) for power spectral density, or "spectrum" for squared magnitude spectrum
    :param window: Window type to use (see https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.windows.get_window.html)

    :return: Tuple containing frequencies array and periodogram array of shape (n_channels, n_frequencies)
    """

    spectral_func = _get_spectral_function_from_name(name=method)
    f, spectrum = spectral_func(data=recording.data, sample_rate=recording.sample_rate, scaling=scaling, window=window)
    return f, spectrum


# Detection functions --------------------------


@enforce_type_hints
def check_for_data_problems(recording: Recording) -> dict[str, list]:
    # TODO: docstring
    dead_channels = detect_dead_channels(recording=recording, std_threshold=constants.DEAD_CHANNEL_SD_THRESHOLD)
    noisy_channels = detect_noisy_channels(recording=recording, variance_threshold=constants.NOISY_CHANNEL_VARIANCE_THRESHOLD)
    nan_channels = detect_nans(recording=recording)
    found_powerline_peaks = detect_powerline_noise(recording=recording,
                                                   power_threshold=constants.POWERLINE_POWER_THRESHOLD,
                                                   baseline_l_freq=constants.BASELINE_FOR_PEAKS_LOW,
                                                   baseline_h_freq=constants.BASELINE_FOR_PEAKS_HIGH)
    # TODO: how to choose good keys?
    return {'Dead channels': dead_channels,
            'Noisy channels': noisy_channels,
            'Channels with missing values': nan_channels,
            'Potential powerline contamination, Hz': found_powerline_peaks}


@enforce_type_hints
@protect_from_lib_error("numpy")
def detect_dead_channels(recording: Recording, std_threshold: float = constants.DEAD_CHANNEL_SD_THRESHOLD) -> list[str]:
    """Detect channels with abnormally low variability (possible dead channels).

    :param recording: Input recording
    :param std_threshold: Standard deviation threshold for flagging the channel as dead

    :return: List of channel names suspected to be dead
    """
    # TODO: check the version with medians (filt_func.py), may be better
    sds = np.std(recording.data, axis=0)
    mean_std = np.mean(sds)
    dead_channels = [ch for i, ch in enumerate(recording.channel_names) if sds[i] < mean_std * std_threshold]
    if dead_channels:
        logger.warning(f'Possibly dead channels detected: {", ".join(dead_channels)}')
    return dead_channels


@enforce_type_hints
@protect_from_lib_error("numpy")
def detect_noisy_channels(recording: Recording, variance_threshold: int | float = constants.NOISY_CHANNEL_VARIANCE_THRESHOLD) -> list[str]:
    """Detect channels with abnormally high variance (likely noisy channels).

    :param recording: Input recording
    :param variance_threshold: Variance threshold multiplier for flagging the channel as noisy

    :return: List of channel names suspected to be noisy
    """
    variances = np.var(recording.data, axis=1)
    mean_var = np.mean(variances)
    noisy_channels = [ch for i, ch in enumerate(recording.channel_names) if variances[i] > mean_var * variance_threshold]
    if noisy_channels:
        logger.info(f'Possibly noisy channels detected (high variance): {", ".join(noisy_channels)}')
    return noisy_channels


@enforce_type_hints
@protect_from_lib_error("numpy")
def detect_nans(recording: Recording) -> list[str]:
    n_nans_per_channel = np.isnan(recording.data).sum(axis=1)
    nan_channels = [ch for i, ch in enumerate(recording.channel_names) if n_nans_per_channel[i] > 0]
    if nan_channels:
        logger.info(f'Found channels with missing data (NaNs): {", ".join(nan_channels)}')
    return nan_channels


@enforce_type_hints
def detect_powerline_noise(recording: Recording, power_threshold: float = constants.POWERLINE_POWER_THRESHOLD,
                           baseline_l_freq: int | float = constants.BASELINE_FOR_PEAKS_LOW,
                           baseline_h_freq: int | float = constants.BASELINE_FOR_PEAKS_HIGH) -> list:
    """Detect powerline noise frequency in a recording.

    :param recording: Input recording
    :param power_threshold: maximum peak/baseline ratio to the peak to be considered having powerline noise

    :return: List of all frequencies which are recommended to remove from data
    """
    f, x = breesy_scipy._si_periodogram(recording.data, recording.sample_rate)
    baseline = _get_baseline_for_peak_detection(f=f, x=x, start_freq=baseline_l_freq, end_freq=baseline_h_freq)

    powerline_found = False
    found_peaks = []

    for freq in [50, 60]:
        if (recording.sample_rate / 2 < freq):
            continue  # freq is higher than Nyquist
        peaks = _measure_peaks_at(f=f, x=x, freq=freq, baseline=baseline)
        if (peaks > power_threshold).any():
            powerline_found = True
            found_peaks.append(freq)
            noisy_channel_names = _get_noisy_channel_names(peaks, recording.channel_names, power_threshold)
            logger.info(
                f'These channels probably contains powerline noise of {freq} Hz:\n'
                f'\t{", ".join(noisy_channel_names)}'
            )

            # harmonics
            for harmonic in range(freq*2, int(recording.sample_rate)//2, freq):
                baseline_h = _get_baseline_for_peak_detection(f=f, x=x, start_freq=harmonic-30, end_freq=harmonic-10)
                peaks = _measure_peaks_at(f=f, x=x, freq=harmonic, baseline=baseline_h)
                if (peaks > power_threshold).any():
                    found_peaks.append(harmonic)
                    noisy_channel_names = _get_noisy_channel_names(peaks, recording.channel_names, power_threshold)
                    logger.info(
                        f'+ harmonics of {harmonic} Hz:\n'
                        f'\t{", ".join(noisy_channel_names)}'
                    )

    if not powerline_found:
        logger.info('No powerline noise detected.')

    return found_peaks


@protect_from_lib_error("numpy")
def _get_baseline_for_peak_detection(f: np.ndarray, x: np.ndarray, start_freq: int | float, end_freq: int | float) -> np.ndarray:
   start_i = np.searchsorted(f, start_freq)
   end_i = np.searchsorted(f, end_freq)
   baseline = np.percentile(x[:, start_i:end_i], q=95, axis=1)
   return baseline


@protect_from_lib_error("numpy")
def _measure_peaks_at(f: np.ndarray, x: np.ndarray, freq: int | float, baseline: float) -> np.ndarray:
    freq_i = np.searchsorted(f, freq)
    return x[:, freq_i] / baseline


def _get_noisy_channel_names(peaks: np.ndarray, ch_names: list[str], power_threshold: float) -> list[str]:
    if len(peaks) != len(ch_names):
        raise BreesyInternalError(f"{len(peaks)=} should equal {len(ch_names)=}", ex=None)
    return [n for n, p in zip(ch_names, peaks) if p > power_threshold]


# ----------------

# TODO: move to a new file called decomposition? or to transform?
@enforce_type_hints
def get_ica_components(recording: Recording, n_components: int, random_state: int | None = None) -> np.ndarray:
    """Compute Independent Component Analysis (ICA) components.

    :param recording: Input recording with data shaped (n_channels, n_samples)
    :param n_components: Number of ICA components to compute
    :param random_state: Optional random seed for reproducibility

    :return: Components array of shape (n_components, n_samples)
    """
    ica = _sklearn_fastica(n_components=n_components, random_state=random_state)
    components = ica.fit_transform(recording.data.T)
    return components.T


# ----------------


@enforce_type_hints
def remove_powerline_noise(recording: Recording, quality_factor: int | float = constants.POWERLINE_NOTCH_QUALITY_FACTOR,
                           power_threshold: float = constants.POWERLINE_POWER_THRESHOLD) -> Recording:
    """Remove powerline noise from a recording.

    :param recording: Input recording
    :param quality_factor: Quality factor for the notch filter

    :return: Filtered recording
    """
    frequency = detect_powerline_noise(recording=recording, power_threshold=power_threshold)
    if frequency:
        return notch_filter(recording=recording, frequency=frequency, quality_factor=quality_factor)
    return recording


@enforce_type_hints
@protect_from_lib_error("numpy")
def mean_centering(recording: Recording) -> Recording:
    """Center the recording data by subtracting the mean.

    :param recording: Input recording

    :return: Mean-centered recording
    """
    new_eeg_data = recording.data - np.expand_dims(recording.data.mean(axis=-1), 1)
    return update_data(recording, new_eeg_data)


@enforce_type_hints
def remove_slow_drift(recording: Recording, highpass_freq: int | float = constants.SLOWDRIFT_REMOVAL_FREQ,
                      filter_order: int = constants.BUTTER_FILTER_ORDER) -> Recording:
    """Remove slow drift using a high-pass Butterworth filter.

    :param recording: Input recording
    :param highpass_freq: High-pass cutoff frequency in Hz
    :param filter_order: Order of the Butterworth high-pass filter

    :return: Filtered recording
    """
    highpass = breesy_scipy._si_butter_highpass_sos(freq=highpass_freq, sample_rate=recording.sample_rate, filter_order=filter_order)
    new_eeg_data = breesy_scipy._si_sosfiltfilt(sos=highpass, data=recording.data)
    return update_data(recording, new_eeg_data)


@enforce_type_hints
@protect_from_lib_error("numpy")
def rereference(recording: Recording, channel_name: str) -> Recording:
    """Re-reference EEG by subtracting a reference signal from each channel.

    :param recording: Input recording
    :param channel_name: Name of the reference signal to subtract

    :return: Re-referenced recording
    """
    ch_i = recording.channel_names.find(channel_name)
    if ch_i == -1:
        available_channels = ", ".join([f'"{x}"' for x in recording.channel_names])
        raise BreesyError(f'Channel "{channel_name}" was not found in recording.',
                          f'Use one of available channels: {available_channels}.')
    new_eeg_data = recording.data - recording.data[ch_i]
    return update_data(recording, new_eeg_data)


def _get_spectral_function_from_name(name: str) -> Callable:
    if name == "welch":
        return _si_welch
    elif name == "periodogram":
        return _si_periodogram
    else:
        raise BreesyError(f'The method "{name}" to get spectral features is either unknown or unsupported.',
                          f'Choose one of supported methods instead: '
                          '"welch" (faster, default) or '
                          '"periodogram" (has better resolution).')
