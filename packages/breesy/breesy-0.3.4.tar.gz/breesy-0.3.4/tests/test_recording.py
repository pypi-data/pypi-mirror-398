from pathlib import Path
from breesy.load import load_recording
from breesy.recording import select_channels, cut_by_second_range

REPO_ROOT = Path(__file__).parent.parent


def test_recording_select_channels():
    # Arrange
    datapath = REPO_ROOT / "tests" / "data" / "alpha" / "subject_01.mat"
    rec = load_recording(str(datapath))

    # Act
    selected = select_channels(rec, ['Channel_2', 'Channel_3', 'Channel_4'])

    # Assert
    assert selected.data.shape[0] == 3
    assert selected.channel_names == ['Channel_2', 'Channel_3', 'Channel_4']
    assert selected.data.shape[1] == rec.data.shape[1]
    assert selected.sample_rate == rec.sample_rate


def test_recording_cut_by_seconds():
    # Arrange
    datapath = REPO_ROOT / "tests" / "data" / "alpha" / "subject_01.mat"
    rec = load_recording(str(datapath))

    # Act
    cut = cut_by_second_range(rec, start_second=0, end_second=10)

    # Assert
    expected_samples = int(10 * rec.sample_rate) + 1
    assert cut.data.shape == (rec.data.shape[0], expected_samples)
    assert cut.sample_rate == rec.sample_rate
    assert cut.channel_names == rec.channel_names


def test_recording_operations_preserve_shape():
    # Arrange
    datapath = REPO_ROOT / "tests" / "data" / "alpha" / "subject_01.mat"
    rec = load_recording(str(datapath))

    # Act
    processed = select_channels(rec, ['Channel_2', 'Channel_5', 'Channel_10'])
    processed = cut_by_second_range(processed, start_second=5, end_second=15)

    # Assert
    expected_samples = int(10 * rec.sample_rate) + 1
    assert processed.data.shape == (3, expected_samples)
    assert processed.sample_rate == rec.sample_rate
    assert len(processed.channel_names) == 3
