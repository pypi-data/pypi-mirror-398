import numpy as np
from matplotlib import pyplot as plt
from scipy import fft

from . import constants
from .errors import protect_from_lib_error
from .type_hints import enforce_type_hints


WAVE_SAMPLE_RATE = constants.PLAYGROUND_WAVE_SAMPLE_RATE
WAVE_T = np.arange(0, constants.PLAYGROUND_WAVE_DURATION, 1/WAVE_SAMPLE_RATE)
SPECTRUM_F = fft.rfftfreq(len(WAVE_T), d=1/WAVE_SAMPLE_RATE)


class Wave:
  def __init__(self, a):
    self.a = np.round(a, constants.PLAYGROUND_Y_ROUND_FACTOR)

  def __add__(self, wave2):
    return Wave(a=self.a+wave2.a)

  def __sub__(self, wave2):
    return Wave(a=self.a-wave2.a)

  def __mul__(self, x: int | float):
    return Wave(a=self.a*x)

  def __truediv__(self, x: int | float):
    return Wave(a=self.a/x)

  def __eq__(self, wave2) -> bool:
    return np.allclose(self.a, wave2.a, rtol=1e-05, atol=1e-08)
  

class Spectrum:
  def __init__(self, s):
    self.s = s

  def __add__(self, spectrum2):
    return Spectrum(s=self.s+spectrum2.s)

  def __sub__(self, spectrum2):
    return Spectrum(s=self.s-spectrum2.s)

  def __mul__(self, x: int | float):
    return Spectrum(s=self.s*x)

  def __truediv__(self, x: int | float):
    return Spectrum(s=self.s/x)

  def __eq__(self, spectrum2) -> bool:
    return np.allclose(self.s, spectrum2.s, rtol=1e-05, atol=1e-08)


@enforce_type_hints
def create_wave(frequency: int | float = 1,
                amplitude: int | float = 1,
                phase: int | float = 0) -> Wave:
    f"""Create a simple sine wave with provided attributes. The wave will have length of {constants.PLAYGROUND_WAVE_DURATION} second and sample rate of {WAVE_SAMPLE_RATE} Hz.

    :param frequency: Frequency in Hz (Default: 1 Hz)
    :param amplitude: Amplitude (Default: 1 arbitrary unit)
    :param phase: Phase of the wave (Default: 0)
    """
    assert frequency <= WAVE_SAMPLE_RATE / 2, f"Default sample rate is {WAVE_SAMPLE_RATE} Hz, so the maximum allowed frequency is {WAVE_SAMPLE_RATE/2} Hz."
    a = amplitude * np.sin(2 * np.pi * frequency * WAVE_T + phase)
    return Wave(a=a)


@enforce_type_hints
@protect_from_lib_error("numpy")
def generate_white_noise(random_state: int | None = None, scale: int | float = 1) -> Wave:
    """Generate Gaussian white noise.

    :param random_state: Random seed for reproducibility
    :param scale: standard deviation of data (Default: 1 arbitrary unit)
    """
    rng = np.random.default_rng(random_state)
    n_samples = len(WAVE_T)
    noise = rng.normal(0, scale, n_samples)
    return Wave(a=noise)


@enforce_type_hints
@protect_from_lib_error("numpy")
def generate_pink_noise(random_state: int | None = None, scale: int | float = 1) -> Wave:
    """Generate pink (1/f) noise.

    :param random_state: Random seed for reproducibility
    :param scale: standard deviation of data (Default: 1 arbitrary unit)
    """
    rng = np.random.default_rng(random_state)
    n_samples = len(WAVE_T)

    white_noise = rng.normal(0, 1, n_samples)
    f = np.fft.fftfreq(n_samples)
    f[0] = np.inf  # Avoid division by zero
    f = np.abs(f)
    pink_noise = np.real(np.fft.ifft(np.fft.fft(white_noise) / np.sqrt(f)))
    pink_noise = pink_noise / np.std(pink_noise) * scale
    # TODO: does scale even do anything here?
    return Wave(a=pink_noise)


@enforce_type_hints
def wave_to_spectrum(wave: Wave) -> Spectrum:
    """Get a spectrum from a sine wave.

    :param wave: a Wave object
    """
    fft_complex = fft.rfft(wave.a)
    return Spectrum(s=fft_complex)


@enforce_type_hints
def spectrum_to_wave(spectrum: Spectrum) -> Wave:
    """Get a sine wave from a spectrum.

    :param spectrum: a Spectrum object
    """
    a = fft.irfft(spectrum.s)
    return Wave(a=a)


@enforce_type_hints
def plot_waves(*args: Wave) -> None:
    """Plot one or more sine waves overlapping in the same plot.

    :param args: one or more Wave objects
    """
    plt.figure(figsize=(12, 4))
    for i, wave in enumerate(args):
        plt.plot(WAVE_T, wave.a, alpha=0.75, lw=2, label=f'wave {i+1}')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')
    plt.xlim(0, constants.PLAYGROUND_WAVE_DURATION)
    plt.legend(bbox_to_anchor=(1, 1))
    plt.grid(alpha=0.6, ls=':')
    plt.box(False)
    plt.tight_layout()
    plt.show()


@enforce_type_hints
def plot_spectrum(spectrum: Spectrum) -> None:
    """Plot a spectrum.

    :param spectrum: one Spectrum object
    """
    plt.figure(figsize=(12, 4))
    power = np.abs(spectrum.s)**2 / len(WAVE_T)
    last_nonzero = max(np.nonzero(power.round(6) > 0)[0])
    if last_nonzero < 100:
        plt.plot(SPECTRUM_F, power, alpha=0.5, lw=1, ls=':', color=constants.COLOR_SPECTRUM)
        plt.scatter(SPECTRUM_F, power, alpha=0.75, lw=2, s=10, color=constants.COLOR_SPECTRUM)
    else:
        plt.plot(SPECTRUM_F, power, alpha=0.75, lw=2, color=constants.COLOR_SPECTRUM)
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Amplitude')

    if last_nonzero + 1 < len(SPECTRUM_F):
      xlim_max = min(SPECTRUM_F[last_nonzero+1] * 1.5, SPECTRUM_F.max())
    else:
       xlim_max = min(SPECTRUM_F[-1] * 1.5, SPECTRUM_F.max())
    plt.xlim(0, xlim_max)
    plt.grid(alpha=0.6, ls=':')
    plt.box(False)
    plt.tight_layout()
    plt.show()
