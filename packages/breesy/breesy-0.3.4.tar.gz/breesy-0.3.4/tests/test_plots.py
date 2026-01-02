from pathlib import Path
from breesy.load import load_recording
from breesy.recording import select_channels
from breesy.plots import (
    plot_recording,
    plot_mean_frequency_spectrum,
    plot_recording_montage,
    plot_mean_topography,
)

REPO_ROOT = Path(__file__).parent.parent
TEST_OUTPUT_DIR = Path(__file__).parent / "test_outputs"

STANDARD_10_10_CHANNELS = [
    'Fp1', 'Fp2', 'F7', 'F3', 'Fz', 'F4', 'F8', 'FC5', 'FC1', 'FC2',
    'FC6', 'T7', 'C3', 'Cz', 'C4', 'T8', 'CP5', 'CP1', 'CP2', 'CP6',
    'P7', 'P3', 'Pz', 'P4', 'P8', 'O1', 'Oz', 'O2'
]


def test_plot_recording():
    # Arrange
    datapath = REPO_ROOT / "tests" / "data" / "alpha" / "subject_01.mat"
    output_path = TEST_OUTPUT_DIR / "plot_recording.png"
    rec = load_recording(str(datapath))

    # Act
    plot_recording(rec, start=0, duration=10, savepath=str(output_path), save_format="png")

    # Assert
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_plot_mean_frequency_spectrum():
    # Arrange
    datapath = REPO_ROOT / "tests" / "data" / "alpha" / "subject_01.mat"
    output_path = TEST_OUTPUT_DIR / "plot_spectrum.png"
    rec = load_recording(str(datapath))

    # Act
    plot_mean_frequency_spectrum(rec, savepath=str(output_path), save_format="png")

    # Assert
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_plot_recording_montage():
    # Arrange
    datapath = REPO_ROOT / "tests" / "data" / "ssvep" / "sub-01_ses-01_task-ssvep_eeg.vhdr"
    output_path = TEST_OUTPUT_DIR / "plot_montage.png"
    rec = load_recording(str(datapath))

    # Act
    plot_recording_montage(rec, savepath=str(output_path), save_format="png")

    # Assert
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_plot_mean_topography():
    # Arrange
    datapath = REPO_ROOT / "tests" / "data" / "ssvep" / "sub-01_ses-01_task-ssvep_eeg.vhdr"
    output_path = TEST_OUTPUT_DIR / "plot_topography.png"
    rec = load_recording(str(datapath))
    rec = select_channels(rec, STANDARD_10_10_CHANNELS)

    # Act
    plot_mean_topography(rec, start=0, duration=1, savepath=str(output_path), save_format="png")

    # Assert
    assert output_path.exists()
    assert output_path.stat().st_size > 0
