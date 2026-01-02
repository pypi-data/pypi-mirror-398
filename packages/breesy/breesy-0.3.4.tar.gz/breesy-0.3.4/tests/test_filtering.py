from pathlib import Path
import numpy as np
from breesy.load import load_recording
from breesy.filtering import notch_filter, select_bandwidth

REPO_ROOT = Path(__file__).parent.parent


def test_notch_filter_removes_powerline():
    # Arrange
    datapath = REPO_ROOT / "tests" / "data" / "alpha" / "subject_01.mat"
    rec = load_recording(str(datapath))

    # Act
    filtered = notch_filter(rec, frequency=50)

    # Assert
    assert filtered.data.shape == rec.data.shape
    assert filtered.sample_rate == rec.sample_rate
    assert filtered.channel_names == rec.channel_names
    assert not np.array_equal(filtered.data, rec.data)


def test_bandpass_filter_applies():
    # Arrange
    datapath = REPO_ROOT / "tests" / "data" / "alpha" / "subject_01.mat"
    rec = load_recording(str(datapath))

    # Act
    filtered = select_bandwidth(rec, low=8, high=13)

    # Assert
    assert filtered.data.shape == rec.data.shape
    assert filtered.sample_rate == rec.sample_rate
    assert filtered.channel_names == rec.channel_names
    assert not np.array_equal(filtered.data, rec.data)


def test_chained_filters():
    # Arrange
    datapath = REPO_ROOT / "tests" / "data" / "alpha" / "subject_01.mat"
    rec = load_recording(str(datapath))

    # Act
    filtered = notch_filter(rec, frequency=50)
    filtered = select_bandwidth(filtered, low=1, high=40)

    # Assert
    assert filtered.data.shape == rec.data.shape
    assert filtered.sample_rate == rec.sample_rate
    assert not np.array_equal(filtered.data, rec.data)
