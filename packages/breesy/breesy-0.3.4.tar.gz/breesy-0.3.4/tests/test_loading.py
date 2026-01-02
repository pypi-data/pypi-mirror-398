"""Tests for loading EEG data in various formats."""

from pathlib import Path
import pytest
from breesy.load import load_recording
from breesy.recording import Recording


def test_load_mat_alpha_dataset():
    """Test loading MAT format using existing alpha dataset.

    This test uses the same subject_01.mat file that students/users can download_example_data("alpha").
    """
    repo_root = Path(__file__).parent.parent
    datapath = repo_root / "tests" / "data" / "alpha" / "subject_01.mat"

    assert datapath.exists(), f"Test data file not found: {datapath}"

    rec = load_recording(str(datapath))

    assert rec is not None, "Recording should not be None"
    assert isinstance(rec, Recording), "Should return a Recording instance"
    assert rec.data is not None, "Recording should have data"
    assert rec.data.ndim == 2, "Data should be 2D (channels x samples)"
    assert rec.sample_rate > 0, "Sample rate should be positive"
    assert len(rec.channel_names) > 0, "Should have channel names"
    assert len(rec.channel_names) == rec.data.shape[0], \
        "Number of channel names should match number of data channels"

    # Format-specific assertions
    assert rec.data.shape == (16, 119808), "Alpha dataset should have 16 channels and 119808 samples"
    assert rec.sample_rate == 512.0, "Alpha dataset sample rate should be 512 Hz"


def test_load_brainvision_ssvep_dataset():
    """Test loading BrainVision format using SSVEP example dataset."""
    repo_root = Path(__file__).parent.parent
    datapath = repo_root / "tests" / "data" / "ssvep" / "sub-01_ses-01_task-ssvep_eeg.vhdr"

    assert datapath.exists(), f"Test data file not found: {datapath}"

    # Verify companion files exist
    eeg_file = datapath.with_suffix('.eeg')
    vmrk_file = datapath.with_suffix('.vmrk')
    assert eeg_file.exists(), f"BrainVision .eeg file not found: {eeg_file}"
    assert vmrk_file.exists(), f"BrainVision .vmrk file not found: {vmrk_file}"

    rec = load_recording(str(datapath))

    assert rec is not None, "Recording should not be None"
    assert isinstance(rec, Recording), "Should return a Recording instance"
    assert rec.data is not None, "Recording should have data"
    assert rec.data.ndim == 2, "Data should be 2D (channels x samples)"
    assert rec.sample_rate > 0, "Sample rate should be positive"
    assert len(rec.channel_names) > 0, "Should have channel names"
    assert len(rec.channel_names) == rec.data.shape[0], \
        "Number of channel names should match number of data channels"

    # Format-specific assertions
    assert rec.data.shape == (32, 469680), "SSVEP dataset should have 32 channels and 469680 samples"
    assert rec.sample_rate == 1000, "SSVEP dataset sample rate should be 1000 Hz"
    assert len(rec.channel_names) == 32, "SSVEP dataset should have 32 channel names"


# Future tests for formats not yet supported
@pytest.mark.skip(reason="EDF format not yet supported by Breesy")
def test_load_edf_schalk_dataset():
    """Test loading EDF format - currently not supported. This is the same schalk dataset that users can download_example_data("schalk").
    """
    repo_root = Path(__file__).parent.parent
    datapath = repo_root / "tests" / "data" / "schalk" / "S001R01.edf"

    # When EDF support is added, uncomment:
    # rec = load_recording(str(datapath))
    # assert rec is not None
    # assert rec.data.shape[0] == 64  # 64 channels
    # assert rec.sample_rate == 160  # 160 Hz


@pytest.mark.skip(reason="EEGLAB .set format not yet supported by Breesy")
def test_load_eeglab_n170_dataset():
    """Test loading EEGLAB format - currently not supported."""
    repo_root = Path(__file__).parent.parent
    datapath = repo_root / "tests" / "data" / "n170" / "1_N170_shifted_ds_reref_ucbip_hpfilt_ica_weighted.set"

    # When EEGLAB support is added, uncomment:
    # rec = load_recording(str(datapath))
    # assert rec is not None
