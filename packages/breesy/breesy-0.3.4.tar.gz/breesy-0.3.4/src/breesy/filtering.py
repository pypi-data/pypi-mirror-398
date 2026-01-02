import numpy as np

from breesy import breesy_scipy, constants
from breesy.recording import Recording
from breesy.breesy_scipy import _si_butter_bandpass_sos, _si_sosfiltfilt
from breesy.errors import BreesyError
from breesy.recording import update_data
from breesy.type_hints import enforce_type_hints


@enforce_type_hints
def notch_filter(recording: Recording, frequency: int | float | list[int | float], method: str = 'fir',
                 quality_factor: int | float = constants.POWERLINE_NOTCH_QUALITY_FACTOR) -> Recording:
    """Apply notch filter to remove a specific frequency from a recording.

    :param recording: Input recording
    :param frequency: Frequency to remove in Hz
    :param method: Filter method to use. Default is FIR ("fir"). Other option is IIR ("iir") which is faster but less suitable for EEG.
    :param quality_factor: Quality factor for the notch filter

    :return: Filtered recording
    """
    if isinstance(frequency, (int, float)):
       frequency = [frequency]

    new_data = recording.data.copy()

    if method == 'fir':
        new_data = _multi_notch_fir(data=new_data, frequencies=frequency, sample_rate=recording.sample_rate,
                                    notch_width=1.0, transition_width=0.5)  # TODO: connect these with quality factor used in iir?
    elif method == 'iir':
        new_data = _multi_notch_iir(data=new_data, frequencies=frequency, sample_rate=recording.sample_rate,
                                    quality_factor=quality_factor)
    else:
        raise BreesyError(f'The filter named "{method}" is unknown or unsupported in Breesy.',
                            'Use one of supported filters: "fir" (recommended, default) or "iir" (faster).')

    return update_data(recording, new_data)


@enforce_type_hints
def select_bandwidth(recording: Recording, low: float | int, high: float | int, filter_order: int = 5) -> Recording:
    """Filter recording to keep only a specific frequency band.

    :param recording: Input recording
    :param low: Lower frequency bound in Hz
    :param high: Upper frequency bound in Hz
    :param filter_order: Order of the filter

    :return: Filtered recording
    """

    # TODO: update function to FIR and unhardcode

    data = recording.data
    sample_rate = recording.sample_rate

    low_high_range_valid = low <= high
    if not low_high_range_valid:
        raise BreesyError("Low frequency bound is higher than the high frequency bound",
                          "Provide a low frequency bound value that is less than or equal to the high frequency bound")

    high_bound_exceeds_nyquist = high >= (sample_rate / 2)
    if high_bound_exceeds_nyquist:
        raise BreesyError("High frequency bound exceeds Nyquist frequency",
                          "Provide a high frequency bound value that is less than half of the sample rate")

    bandpass = _si_butter_bandpass_sos(low, high, sample_rate, filter_order)

    new_eeg_data = _si_sosfiltfilt(bandpass, data)

    return update_data(recording, new_eeg_data)


def _multi_notch_fir(data: np.ndarray, frequencies: list[float | int], sample_rate: int | float,
                        notch_width: float, transition_width: float) -> np.ndarray:
    bands = [x for freq in frequencies for x in (freq-notch_width/2, freq+notch_width/2)]
    numtaps = int(sample_rate / transition_width)
    numtaps = numtaps if numtaps % 2 == 1 else numtaps + 1
    fir_coeff = breesy_scipy._si_firwin_bandstop_multibands(numtaps=numtaps, bands=bands, sample_rate=sample_rate)
    filtered_data = breesy_scipy._si_filtfilt(fir_coeff, [1], data)
    return filtered_data


def _multi_notch_iir(data: np.ndarray, frequencies: list[float | int], sample_rate: int | float,
                        quality_factor: int | float) -> np.ndarray:
    for freq in frequencies:
        b, a = breesy_scipy._si_iirnotch(freq=freq, quality_factor=quality_factor, sample_rate=sample_rate)
        data = breesy_scipy._si_filtfilt(b=b, a=a, data=data)
    return data
