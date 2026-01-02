from pathlib import Path
import numpy as np
from breesy.load import load_recording
from breesy.features import get_mean_power
from breesy.recording import split_by_window_duration

REPO_ROOT = Path(__file__).parent.parent


def test_mean_power_alpha_band():
    # Arrange
    datapath = REPO_ROOT / "tests" / "data" / "alpha" / "subject_01.mat"
    rec = load_recording(str(datapath))
    epochs = split_by_window_duration(rec, window_duration=5.0)
    epoch_data = np.array([epoch.data for epoch in epochs])

    # Act
    alpha_power = get_mean_power(epoch_data, freq_range='alpha', sample_rate=rec.sample_rate)

    # Assert
    assert alpha_power.ndim == 1
    assert alpha_power.shape[0] == len(epochs)
    assert np.all(alpha_power > 0)
    assert np.all(np.isfinite(alpha_power))


def test_mean_power_custom_range():
    # Arrange
    datapath = REPO_ROOT / "tests" / "data" / "alpha" / "subject_01.mat"
    rec = load_recording(str(datapath))
    epochs = split_by_window_duration(rec, window_duration=5.0)
    epoch_data = np.array([epoch.data for epoch in epochs])

    # Act
    power = get_mean_power(epoch_data, freq_range=(10, 15), sample_rate=rec.sample_rate)

    # Assert
    assert power.ndim == 1
    assert power.shape[0] == len(epochs)
    assert np.all(power > 0)
    assert np.all(np.isfinite(power))


def test_frequency_bands():
    # Arrange
    datapath = REPO_ROOT / "tests" / "data" / "alpha" / "subject_01.mat"
    rec = load_recording(str(datapath))
    epochs = split_by_window_duration(rec, window_duration=5.0)
    epoch_data = np.array([epoch.data for epoch in epochs])
    bands = ['delta', 'theta', 'alpha', 'beta', 'gamma']

    # Act & Assert
    for band in bands:
        power = get_mean_power(epoch_data, freq_range=band, sample_rate=rec.sample_rate)

        assert power.ndim == 1
        assert power.shape[0] == len(epochs)
        assert np.all(power > 0)
        assert np.all(np.isfinite(power))
