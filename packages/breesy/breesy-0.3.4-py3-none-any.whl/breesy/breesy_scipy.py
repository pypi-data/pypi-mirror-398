import numpy as np
from scipy import signal as si
from scipy.interpolate import RBFInterpolator

from .errors import protect_from_lib_error
from . import constants


@protect_from_lib_error("scipy")
def _si_welch(data: np.ndarray, sample_rate: int | float, window: str | None = None,
              scaling: str = 'density', average: str = 'mean') -> tuple[np.ndarray, np.ndarray]:
    window = window or 'hann'
    return si.welch(x=data, fs=sample_rate, window=window, scaling=scaling, average=average, axis=-1)


@protect_from_lib_error("scipy")
def _si_periodogram(data: np.ndarray, sample_rate: int | float, window: str | None = None,
                    scaling: str = 'density') -> tuple[np.ndarray, np.ndarray]:
    window = window or 'boxcar'
    return si.periodogram(x=data, fs=sample_rate, window=window, scaling=scaling, axis=-1)


@protect_from_lib_error("scipy")
def _si_filtfilt(b, a, data: np.ndarray) -> np.ndarray:
    return si.filtfilt(b=b, a=a, x=data, axis=-1)


@protect_from_lib_error("scipy")
def _si_sosfiltfilt(sos: np.ndarray, data: np.ndarray) -> np.ndarray:
    return si.sosfiltfilt(sos=sos, x=data)


@protect_from_lib_error("scipy")
def _si_butter_bandpass_sos(low: float, high: float, sample_rate: int | float,
                            filter_order: int = constants.BUTTER_FILTER_ORDER) -> np.ndarray:
    return si.butter(N=filter_order, Wn=(low, high), btype='bandpass', output='sos', fs=sample_rate, analog=False)
    # with "sos", always returns single np.ndarray


@protect_from_lib_error("scipy")
def _si_butter_lowpass_sos(freq: float, sample_rate: int | float,
                           filter_order: int = constants.BUTTER_FILTER_ORDER) -> np.ndarray:
    return si.butter(N=filter_order, Wn=freq, btype='lowpass', output='sos', fs=sample_rate, analog=False)
    # with "sos", always returns single np.ndarray


@protect_from_lib_error("scipy")
def _si_butter_highpass_sos(freq: float, sample_rate: int | float,
                            filter_order: int = constants.BUTTER_FILTER_ORDER) -> np.ndarray:
    return si.butter(N=filter_order, Wn=freq, btype='highpass', output='sos', fs=sample_rate, analog=False)
    # with "sos", always returns single np.ndarray


@protect_from_lib_error("scipy")
def _si_firwin_bandpass_multibands(numtaps: int, bands: list[int | float], sample_rate: int | float, window: str | None = None):
    window = window or "hamming"
    return si.firwin(numtaps=numtaps, cutoff=bands, window=window, pass_zero=False, fs=sample_rate)


@protect_from_lib_error("scipy")
def _si_firwin_bandstop_multibands(numtaps: int, bands: list[int | float], sample_rate: int | float, window: str | None = None):
    window = window or "hamming"
    return si.firwin(numtaps=numtaps, cutoff=bands, window=window, pass_zero='bandstop', fs=sample_rate)


@protect_from_lib_error("scipy")
def _si_iirnotch(freq: float, quality_factor: float, sample_rate: int | float) -> tuple[np.ndarray, np.ndarray]:
    return si.iirnotch(w0=freq, Q=quality_factor, fs=sample_rate)


@protect_from_lib_error("scipy")
def _si_get_rbf_interpolator(coords_arr: np.ndarray, values_arr: np.ndarray) -> RBFInterpolator:
    return RBFInterpolator(coords_arr, values_arr, kernel='thin_plate_spline')