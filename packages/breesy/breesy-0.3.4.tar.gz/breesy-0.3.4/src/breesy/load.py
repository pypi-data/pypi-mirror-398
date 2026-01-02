from pathlib import Path, PosixPath

import numpy as np
# from mne.io.brainvision.brainvision import RawBrainVision
# from mne.io.edf.edf import RawEDF, RawGDF
# from mne.io.eeglab.eeglab import RawEEGLAB

from .logging import logger
from .recording import Recording
from .Event import Event
from .RecordingMetadata import RecordingMetadata
from .constants import EEG_MONTAGES
from .errors import BreesyError, BreesyInternalError, protect_from_lib_error
from .load_events import find_and_load_event_for_file
from .type_hints import enforce_type_hints

# Note: if changing this, then update load_dataset if/else statement as well
# SUPPORTED_FILE_EXTENSIONS = ['.gdf', '.bdf', '.eeg', '.csv', '.mat', '.tsv', '.vhdr', '.npy']
SUPPORTED_FILE_EXTENSIONS = ['.csv', '.mat', '.tsv', '.npy', '.eeg', '.vhdr', '.avg', '.seg']


@enforce_type_hints
def load_recording(filename: str | Path | PosixPath, sample_rate: int | float | None = None) -> Recording:
    """Load a recording from a file with a supported extension.

    :param filename: Path to the file to load
    :param sample_rate: Optional sampling rate in Hz

    :return: Recording object containing the loaded data
    """
    filename = str(filename)
    file_extension = Path(filename).suffix
    if not file_extension:
        raise BreesyError("File name should contain an extension",
                          "Provide a file with a supported extension, example: 'my_data.gdf'")

    is_supported_extension = file_extension in SUPPORTED_FILE_EXTENSIONS
    if not is_supported_extension:
        raise BreesyError(f"Unsupported file extension: {file_extension}",
                          "Provide a file with a supported extension, example: 'my_data.gdf'. "
                          f"Currently supported extensions: {SUPPORTED_FILE_EXTENSIONS}")

    path_filename = Path(filename)
    is_valid_filename = Path.is_file(path_filename)
    if not is_valid_filename:
        raise BreesyError(
            f"File not found: {filename}", "a) Make sure that the file is in your working directory; "
                                           f"the current working directory is: {Path.cwd()}. "
                                           f"b) Double check that your file explorer is showing the full file name "
                                           f"- Windows does not show file extensions by default.")

    # if file_extension == '.gdf':
    #     return load_gdf(filename)
    # elif file_extension == '.bdf':
    #     return load_bdf(filename)
    elif file_extension in ['.eeg', '.avg', '.seg', '.vhdr']:
        from .load_brainvision import load_brainvision_eeg
        return load_brainvision_eeg(filename)
    elif file_extension == '.csv':
        return load_csv(filename)
    elif file_extension == '.mat':
        return load_mat(filename, sample_rate=sample_rate)
    elif file_extension == '.tsv':
        return load_tsv(filename)
    elif file_extension == '.npy':
        return load_numpy(filename)
    else:
        raise BreesyInternalError("File extension valid but not handled")


# @enforce_type_hints
# def load_gdf(filename: str):
#     """Load a GDF file.

#     :param filename: Path to the GDF file

#     :return: Recording object containing the loaded data
#     """
#     raw = _read_raw_gdf(filename)
#     return _convert_mne_to_recording(raw, filename)

# @enforce_type_hints
# def load_bdf(filename: str):
#     """Load a BDF file.

#     :param filename: Path to the BDF file

#     :return: Recording object containing the loaded data
#     """
#     raw = _read_raw_bdf(filename)
#     return _convert_mne_to_recording(raw, filename)

# @enforce_type_hints
# def load_eeglab_eeg(filename: str):
#     """Load an EEGLAB EEG file.

#     :param filename: Path to the EEG file

#     :return: Recording object containing the loaded data
#     """
#     raw = _read_raw_eeglab(filename)
#     return _convert_mne_to_recording(raw, filename)


def _mat_extract_meaningful_keys(mat_data: dict) -> list[str]:
    keys = [k for k in mat_data.keys() if not k.startswith('__')]
    if not keys:
        raise BreesyError(
            "No valid data found. The MATLAB file appears to be empty or contains only metadata."
        )
    elif len(keys) == 1:
        logger.warning(
            "data file likely contains only the recording and "
            "no useful metadata. Please find the sample rate and channel names "
            "in your data description."
        )  # TODO: fast instructions or link to documentation
    return keys


@enforce_type_hints
def load_mat(filename: str, sample_rate: int | float | None = None) -> Recording:
    """Load a MATLAB .mat file.

    :param filename: Path to the .mat file
    :param sample_rate: Sampling rate in Hz

    :return: Recording object containing the loaded data
    """
    mat_data = _loadmat(filename)

    meaningful_keys = _mat_extract_meaningful_keys(mat_data)

    data_key = None

    if len(meaningful_keys) == 1:
        data_key = meaningful_keys[0]
    else:
        # Find the largest array that looks like EEG data
        largest_size = 0
        for key in meaningful_keys:
            value = mat_data[key]
            if isinstance(value, np.ndarray) and value.size > largest_size and value.ndim >= 2:
                largest_size = value.size
                data_key = key

    data = mat_data[data_key]  # TODO: there can be 'O' types, as AI previously suggested?
    if not isinstance(data, np.ndarray):
        raise BreesyError(
            f"Problem reading data which is of type {type(data)}. It may be that Breesy failed to read the file correctly."  # TODO: test different files
        )
    if data.ndim != 2:
        raise BreesyError(
            "Found data has an incorrect number of dimensions. "
            "Expected data.ndim to be 2, but got "
            f"{data.ndim} dimensions instead.",
            "The data may be not EEG data, "
            "there are several records joined into one file, "
            "or Breesy did not found the correct data array in the file."
        )

    if data.shape[0] > data.shape[1]:
        logger.warning("The first data dimension seems to be the samples, because data contains more rows than columns. Dimensions will be switched places.")
        data = data.T
    n_channels, n_samples = data.shape
    default_channel_names = [f'Channel_{i + 1}' for i in range(data.shape[0])]

    # find or create channel names
    channel_name_keys = _find_keys_in_data(meaningful_keys, ['ch', 'ch name', 'ch names', 'channel names', 'channels', 'names', '10-20', '10-10', 'pos', 'positions'])
    if len(channel_name_keys) == 0:
        channel_names = default_channel_names
        channel_name_key = None
    elif len(channel_name_keys) > 1:
        logger.warning(
            "found several keys in data which may contain channel names: "
            f"{channel_name_keys}. "
            "Using the first one.")
        channel_name_key = channel_name_keys[0]
    else:
        channel_name_key = channel_name_keys[0]

    if channel_name_key:
        found_names = mat_data[channel_name_key]
        if not isinstance(found_names, (list, tuple, np.ndarray)):
            logger.warning(
                "found channel name information does not appear to be a list: "
                f"{found_names}. "
                "Default channel names will be used instead.")
            channel_names = default_channel_names
        elif (n_channels != len(found_names)) and (n_samples != len(found_names)):
            logger.warning(
                f"the number of channel names ({len(found_names)}) provided does not match the "
                f"number of channels ({n_channels}) in the EEG data. "
                "Default channel names will be used instead."
            )
            channel_names = default_channel_names
        elif (n_channels != len(channel_names)) and (n_samples == len(channel_names)):
            logger.warning('data rows and columns will be switched places according to the number of found channel names.')
            data = data.T
            n_channels, n_samples = data.shape
            channel_names = found_names
        else:
            channel_names = found_names

    if sample_rate:
        logger.info(f"Overwriting sample rate to {sample_rate}")
        sample_rate = float(sample_rate)
    else:
        # try to find it in keys
        sample_rate = _detect_sample_rate_in_mat_keys(mat_data, meaningful_keys)
        if not sample_rate:
            # try to calculate it from time channel, if present
            sample_rate = _detect_sample_rate_from_time_column(data)
            if not sample_rate:
                raise BreesyError(
                    "No info found about sample rate.",
                    "Please find the recording's sample rate in data description and set manually by "
                    "passing an additional parameter 'sample_rate' into the data loading function. "
                    "Example: load_recording(path, sample_rate=128)."
                )

    data, channel_names = _leave_only_eeg_channels(data, channel_names)
    # channel names may not start from 1 after this, but maybe we should leave it like this

    metadata = RecordingMetadata(
        name=Path(filename).stem,
        file_path=Path(filename),
        description=f"MATLAB data loaded from {filename}"
    )

    return Recording(
        data=data,
        channel_names=channel_names,
        sample_rate=sample_rate,
        events=None,  # No events for now - could be added as a separate function
        metadata=metadata
    )


@enforce_type_hints
def load_delimited_text(filename: str, delimiter: str = ',', sample_rate: int | float | None = None) -> Recording:
    """Load a delimited text file (CSV, TSV, etc.).

    :param filename: Path to the text file
    :param delimiter: Character used to separate values in the file
    :param sample_rate: Sampling rate in Hz. If not provided, will attempt to guess from time column. If sample rate cannot be guessed, an error will be raised.

    :return: Recording object containing the loaded data
    """
    import csv

    # First pass: read headers and determine structure
    with open(filename, 'r', newline='') as file:
        reader = csv.reader(file, delimiter=delimiter)
        headers = next(reader)  # Get column names

        # Check if first column might be time
        time_column_idx = None
        if headers[0].lower() in ['time', 't', 'timestamp']:
            time_column_idx = 0

        # Exclude time column from channel names if present
        if time_column_idx is not None:
            channel_names = headers[1:]
        else:
            channel_names = headers

        # Count rows for pre-allocation
        row_count = sum(1 for _ in reader)

    # Second pass: read all data
    with open(filename, 'r', newline='') as file:
        reader = csv.reader(file, delimiter=delimiter)
        next(reader)  # Skip header

        # Pre-allocate data array
        data = np.zeros((len(channel_names), row_count))
        time_values = None

        if time_column_idx is not None:
            time_values = np.zeros(row_count)

        # Fill data
        for i, row in enumerate(reader):
            if i >= row_count:
                break

            # Convert values to float, handling potential errors
            try:
                row_values = [float(val) for val in row]
            except ValueError:
                # Skip rows that can't be converted to float
                continue

            if time_column_idx is not None:
                time_values[i] = row_values[time_column_idx]
                data_values = row_values[:time_column_idx] + row_values[time_column_idx + 1:]
            else:
                data_values = row_values

            for j, val in enumerate(data_values):
                if j < len(channel_names):
                    data[j, i] = val

    if sample_rate is not None:
        sample_rate = float(sample_rate)
    else:
        if time_values is not None and len(time_values) > 1:
            # Estimate sample rate
            time_diffs = np.diff(time_values)
            avg_diff = float(np.mean(time_diffs))
            if avg_diff > 0:
                sample_rate = float(round(1.0 / avg_diff))
        
        if sample_rate is None:
            raise BreesyError(
                "Sample rate was not provided and it could not be guessed from the data. "
                "Please provide the sample rate manually by passing the 'sample_rate' parameter.",
                "Provide the sample rate as a named argument to the function, e.g.: load_delimited_text('file.csv', sample_rate=500)"
            )

    # Create metadata
    metadata = RecordingMetadata(
        name=Path(filename).stem,
        file_path=Path(filename),
        description=f"Data loaded from {filename}"
    )

    # Look for event columns (columns with mostly 0s and few 1s)
    events = []
    for i, col_name in enumerate(channel_names):
        col_data = data[i, :]
        unique_vals = set(np.unique(col_data))
        # Check if column is binary and sparse (potential event marker)
        if unique_vals <= {0, 1} and np.mean(col_data) < 0.1:
            event_indices = np.where(col_data == 1)[0]
            for idx in event_indices:
                events.append(Event(name=col_name, index=idx))

    return Recording(
        data=data,
        channel_names=channel_names,
        sample_rate=sample_rate,
        events=events,
        metadata=metadata
    )

# Wrapper functions for backward compatibility
@enforce_type_hints
def load_csv(filename: str) -> Recording:
    """Load a CSV file.

    :param filename: Path to the CSV file

    :return: Recording object containing the loaded data
    """
    return load_delimited_text(filename, delimiter=',')


@enforce_type_hints
def load_tsv(filename: str) -> Recording:
    """Load a TSV file.

    :param filename: Path to the TSV file

    :return: Recording object containing the loaded data
    """
    return load_delimited_text(filename, delimiter='\t')


# Note: mostly LLM generated, looks reasonable
@enforce_type_hints
def load_numpy(filename: str, sample_rate: int | float | None = None) -> Recording:
    """Load a numpy .npy file.

    :param filename: Path to the .npy file
    :param sample_rate: Sampling rate in Hz. If None, defaults to 1000 Hz.

    :return: Recording object containing the loaded data
    """
    # Load the NumPy array with error protection
    data = _np_load(filename)

    # TODO: #12 we need to handle this case properly, currently just taking first trial
    if data.ndim == 3:
        # likely many recordings instead of one
        data = data[0]

    # Ensure it's a 2D array
    if data.ndim != 2:
        raise BreesyError(
            f"The NumPy array has {data.ndim} dimensions, but 2 dimensions are required.",
            "Make sure the NumPy file contains a 2D array with shape (channels, samples)."
        )

    # If the first dimension is larger, assume it's (samples, channels) and transpose
    if data.shape[0] > data.shape[1]:
        logger.warning("The first data dimension seems to be the samples, because data contains more rows than columns. Dimensions will be switched places.")
        data = data.T

    # Create default channel names
    channel_names = [f'Channel_{i+1}' for i in range(data.shape[0])]

    if sample_rate is None:
        logger.warning("No sample rate provided. Using default of 1000 Hz.")
        sample_rate = 1000
    else:
        sample_rate = float(sample_rate)

    # Create metadata
    metadata = RecordingMetadata(
        name=Path(filename).stem,
        file_path=Path(filename),
        description=f"NumPy data loaded from {filename}"
    )

    # Find and load events if available
    events = find_and_load_event_for_file(filename, sample_rate)

    return Recording(
        data=data,
        channel_names=channel_names,
        sample_rate=sample_rate,
        events=events,
        metadata=metadata
    )


@enforce_type_hints
def from_array(data: np.ndarray, sample_rate: int | float | None = None, channel_names: list[str] | None = None) -> Recording:
    """Convert a numpy array into a Recording object.

    :param data: NumPy array containing EEG data. Should be 2D with shape (channels, samples) or (samples, channels).
                 If a time column is detected, it will be used to extract the sample rate and removed from the data.
    :param sample_rate: Sampling rate in Hz. If not provided, will attempt to detect from time column.
                        If no time column is found and sample_rate is None, an error will be raised.
    :param channel_names: List of channel names. If not provided, default names will be generated.

    :return: Recording object containing the loaded data
    """
    # Ensure it's a 2D array
    if data.ndim != 2:
        raise BreesyError(
            f"The NumPy array has {data.ndim} dimensions, but 2 dimensions are required.",
            "Make sure the NumPy array is 2D with shape (channels, samples) or (samples, channels)."
        )

    # Auto-transpose if the first dimension is larger (likely samples, channels)
    if data.shape[0] > data.shape[1]:
        logger.warning("The first data dimension seems to be the samples, because data contains more rows than columns. Dimensions will be switched places.")
        data = data.T

    # Check for time column and extract sample rate if needed
    time_column_idx = None
    extracted_sample_rate = None

    for i in range(data.shape[0]):
        if _is_likely_time_column(data[i]):
            time_column_idx = i
            time_step = float(data[i, 1] - data[i, 0])
            extracted_sample_rate = float(1 / time_step)
            logger.info(f"Detected time column at index {i}. Extracted sample rate: {extracted_sample_rate} Hz")
            break

    # Remove time column from data if found
    if time_column_idx is not None:
        data = np.delete(data, time_column_idx, axis=0)

    # Determine final sample rate
    if sample_rate is not None:
        if extracted_sample_rate is not None and abs(sample_rate - extracted_sample_rate) > 0.01:
            logger.warning(f"Warning: Provided sample_rate ({sample_rate} Hz) differs from extracted sample rate ({extracted_sample_rate} Hz). Using the provided sample_rate.")
        sample_rate = float(sample_rate)
    elif extracted_sample_rate is not None:
        sample_rate = extracted_sample_rate
    else:
        raise BreesyError(
            "No sample rate provided and could not detect sample rate from data.",
            "Please provide the sample rate manually by passing the 'sample_rate' parameter. "
            "Example: from_array(data, sample_rate=250)"
        )

    # Create channel names
    if channel_names is None:
        channel_names = [f'Channel_{i+1}' for i in range(data.shape[0])]
    elif len(channel_names) != data.shape[0]:
        raise BreesyError(
            f"The number of channel names ({len(channel_names)}) does not match the number of channels ({data.shape[0]}) in the data.",
            "Make sure that the number of channel names matches the number of channels in the data. "
            f"Expected {data.shape[0]} channel names."
        )

    # Create metadata
    metadata = RecordingMetadata(
        name="NumPy Recording",
        file_path=None,
        description="Recording created from NumPy array"
    )

    return Recording(
        data=data,
        channel_names=channel_names,
        sample_rate=sample_rate,
        events=None,
        metadata=metadata
    )

# # Note: LLM generated, looks reasonable
# @enforce_type_hints
# def load_brainvision_eeg(filename: str) -> Recording:
#     """Load a BrainVision EEG file.

#     :param filename: Path to the BrainVision file (.vhdr)

#     :return: Recording object containing the loaded data
#     """
#     file_path = Path(filename)

#     # Ensure the file exists
#     if not file_path.exists():
#         raise BreesyError(
#             f"File not found: {filename}", "a) Make sure that the file is in your working directory; "
#                                            f"the current working directory is: {Path.cwd()}. "
#                                            f"b) Double check that your file explorer is showing the full file name "
#                                            f"- Windows does not show file extensions by default.")

#     # Determine which file we're dealing with
#     if file_path.suffix.lower() == '.eeg':
#         # If .eeg file provided, look for the corresponding .vhdr
#         vhdr_path = file_path.with_suffix('.vhdr')
#         if not vhdr_path.exists():
#             raise BreesyError(
#                 f"Header file not found for {filename}",
#                 "BrainVision files require a .vhdr file. Make sure it's in the same directory as the .eeg file."
#             )
#         filename = str(vhdr_path)
#     elif file_path.suffix.lower() != '.vhdr':
#         raise BreesyError(
#             f"Unsupported BrainVision file extension: {file_path.suffix}",
#             "Please provide a .vhdr or .eeg file."
#         )

#     # Load the EEG data using MNE
#     raw = _read_raw_brainvision(filename)

#     return _convert_mne_to_recording(raw, filename)

# @enforce_type_hints
# def load_all_files_in_folder_by_extension(file_extension: str, folder_path: str = ""):
#     """Load all files with a specific extension from a folder.

#     :param file_extension: File extension to filter by (e.g., '.mat')
#     :param folder_path: Path to the folder containing the files

#     :return: List of Recording objects containing the loaded data
#     """
#     if not isinstance(folder_path, str):
#         raise BreesyError("Invalid folder_path argument type",
#                           "Provide a string as the folder path, example: 'data_folder', or '' (empty string or period) for current working directory.")

#     if not isinstance(file_extension, str):
#         raise BreesyError("Invalid file_extension argument type",
#                           "Provide a string as the file extension, example: '.gdf'")

#     folder = Path(folder_path)
#     if not folder.is_dir():
#         raise BreesyError(f"The folder path was not found: {folder.resolve()}",
#                           f"Check the folder path manually to make sure that the folder actually exists.")

#     full_path = folder.resolve()

#     files = list(full_path.glob(f"*{file_extension}"))
#     if not files:
#         raise BreesyError(
#             f"No {file_extension} files found in folder: '{folder_path}' (resolved absolute path: {folder.resolve()})",
#             f"Check the folder to make sure that it actually contains {file_extension} files.")

#     data_list = []
#     for file in files:
#         data = load_dataset(str(file))
#         data_list.append(data)

#     return data_list


# @enforce_type_hints
# def load_all_mat_files_in_folder(folder_path: str = ""):
#     """Load all MATLAB .mat files from a folder.

#     :param folder_path: Path to the folder containing the files

#     :return: List of Recording objects containing the loaded data
#     """
#     return load_all_files_in_folder_by_extension(".mat", folder_path)


# @enforce_type_hints
# def load_all_gdf_files_in_folder(folder_path: str = ""):
#     """Load all GDF files from a folder.

#     :param folder_path: Path to the folder containing the files

#     :return: List of Recording objects containing the loaded data
#     """
#     return load_all_files_in_folder_by_extension(".gdf", folder_path)


# @enforce_type_hints
# def load_all_bdf_files_in_folder(folder_path: str = ""):
#     """Load all BDF files from a folder.

#     :param folder_path: Path to the folder containing the files

#     :return: List of Recording objects containing the loaded data
#     """
#     return load_all_files_in_folder_by_extension(".bdf", folder_path)


# @enforce_type_hints
# def load_all_eeg_files_in_folder(folder_path: str = ""):
#     """Load all EEG files from a folder.

#     :param folder_path: Path to the folder containing the files

#     :return: List of Recording objects containing the loaded data
#     """
#     return load_all_files_in_folder_by_extension(".eeg", folder_path)


# @enforce_type_hints
# def load_all_csv_files_in_folder(folder_path: str = ""):
#     """Load all CSV files from a folder.

#     :param folder_path: Path to the folder containing the files

#     :return: List of Recording objects containing the loaded data
#     """
#     return load_all_files_in_folder_by_extension(".csv", folder_path)


# @enforce_type_hints
# def load_all_tsv_files_in_folder(folder_path: str = ""):
#     """Load all TSV files from a folder.

#     :param folder_path: Path to the folder containing the files

#     :return: List of Recording objects containing the loaded data
#     """
#     return load_all_files_in_folder_by_extension(".tsv", folder_path)

# @enforce_type_hints
# def load_all_brainvision_files_in_folder(folder_path: str = ""):
#     """Load all BrainVision files from a folder.

#     :param folder_path: Path to the folder containing the files

#     :return: List of Recording objects containing the loaded data
#     """
#     return load_all_files_in_folder_by_extension(".eeg", folder_path)


# @enforce_type_hints
# def load_all_numpy_files_in_folder(folder_path: str = ""):
#     """Load all NumPy .npy files from a folder.

#     :param folder_path: Path to the folder containing the files

#     :return: List of Recording objects containing the loaded data
#     """
#     return load_all_files_in_folder_by_extension(".npy", folder_path)

# --------- Helper functions ---------

@protect_from_lib_error("numpy")
def _np_load(filename):
    return np.load(filename)

# @protect_from_lib_error("mne")
# def _read_raw_gdf(filename):
#     from mne.io import read_raw_gdf
#     return read_raw_gdf(filename, verbose=False)

# @protect_from_lib_error("mne")
# def _read_raw_bdf(filename):
#     from mne.io import read_raw_bdf
#     return read_raw_bdf(filename, verbose=False)

# @protect_from_lib_error("mne")
# def _read_raw_eeglab(filename):
#     from mne.io import read_raw_eeglab
#     return read_raw_eeglab(filename, verbose=False)

# @protect_from_lib_error("mne")
# def _read_raw_brainvision(filename: str):
#     from mne.io import read_raw_brainvision
#     return read_raw_brainvision(filename, verbose=False)

@protect_from_lib_error("scipy")
def _loadmat(filename):
    from scipy.io import loadmat
    return loadmat(filename, squeeze_me=True)

# def _convert_mne_to_recording(raw: RawGDF | RawEDF | RawEEGLAB | RawBrainVision, filename):
#     data = raw.get_data()
#     sample_rate = int(raw.info['sfreq'])
#     channel_names = raw.ch_names

#     # Extract events if available
#     events = []
#     try:
#         # Use MNE to find events
#         from mne import find_events
#         mne_events = find_events(raw)
#         for event in mne_events:
#             sample_idx = event[0]
#             event_id = event[2]
#             event_name = raw.event_id.get(event_id, f"Event_{event_id}")
#             events.append(Event(name=event_name, index=sample_idx))
#     except Exception as e:
#         pass
#     if not events:
#         print("Events not found through mne.find_events")

#     # Try from annotations
#     if not events:
#         try:
#             from mne import events_from_annotations
#             mne_events, event_id = events_from_annotations(raw)
#             # Map event IDs to event names
#             id_to_name = {v: k for k, v in event_id.items()}

#             for event in mne_events:
#                 sample_idx = event[0]
#                 event_code = event[2]
#                 event_name = id_to_name.get(event_code, f"Event_{event_code}")
#                 events.append(Event(name=event_name, index=sample_idx))
#         except Exception as e:
#             pass
#     if not events:
#         print("Events not found through mne.events_from_annotations")

#     # Extract events for peer files
#     # TODO: maybe this needs to be used in ALL load functions
#     if not events:
#         try:
#             events = find_and_load_event_for_file(filename, sample_rate)
#         except Exception as e:
#             pass
#     if not events:
#         print("Events not found in related files")

#     metadata = RecordingMetadata(
#         name=Path(filename).stem,
#         file_path=Path(filename),
#         description=f"Data loaded from {filename}"
#     )

#     return Recording(
#         data=data,
#         channel_names=channel_names,
#         sample_rate=sample_rate,
#         events=events,
#         metadata=metadata
#     )


def _detect_sample_rate_in_mat_keys(mat_data: dict, keys: list[str]) -> float | None:
    sample_rate_keys = _find_keys_in_data(keys, ['sample rate', 'sp', 'sr', 'hz', 'sampling rate', 'sfreq', 'fs', 'srate'])
    if len(sample_rate_keys) == 0:
        return None

    sample_rate_key = sample_rate_keys[0]
    if len(sample_rate_keys) > 1:
        logger.warning(
            "found several keys in data which may contain sample rate:"
            f"\n{sample_rate_keys}\n"
            "Using the first one.")

    sr_value = mat_data[sample_rate_key]
    try:
        if isinstance(sr_value, (int, float, str)):
            return float(sr_value)
        elif isinstance(sr_value, np.ndarray) and sr_value.size == 1:
            return float(sr_value.item())
        elif isinstance(sr_value, (list, tuple)) and len(sr_value) == 1:
            return float(sr_value[0])
        else:
            raise ValueError
    except ValueError:
        logger.warning(
            f"information found in column {sample_rate_key} "
            "could not be read automatically. Mentioned column contents are:"
            f"\n{sr_value}\n"
            "Sample rate was not set."
        )
        return None


def _detect_sample_rate_from_time_column(data: np.ndarray) -> float | None:
    for i in range(data.shape[0]):
        if _is_likely_time_column(data[i]):
            time_step = float(data[i, 1] - data[i, 0])
            sample_rate = float(1 / time_step)
            return sample_rate
    return None


def _is_likely_eeg_column(column: np.ndarray) -> bool:
    return (not _column_is_monotonic(column)) and (not _column_is_sparse(column))


def _is_likely_time_column(column: np.ndarray) -> bool:
    u_diffs = np.unique(np.diff(column).round(6))
    if len(u_diffs) == 1 and u_diffs[0] > 0:
        return True
    return False


def _leave_only_eeg_channels(data: np.ndarray, ch_names: list[str]) -> tuple[np.ndarray, list[str]]:
    eeg_ix = [i for i in range(data.shape[0]) if _is_likely_eeg_column(data[i])]
    new_channel_names = [x for i, x in enumerate(ch_names) if i in eeg_ix]
    return data[eeg_ix], new_channel_names


def _column_has_eeg_name(column_name: str) -> bool:
    # TODO: #13 should not be case-sensitive?
    return column_name in EEG_MONTAGES['10-10']


def _column_is_monotonic(column: np.ndarray) -> bool:
    diffs = np.diff(column)
    return bool(np.all(diffs >= 0))


def _column_is_sparse(column: np.ndarray, sparsity_threshold: float = 0.2) -> bool:
    u_values, u_counts = np.unique(column, return_counts=True)
    most_common_value_rate = np.max(u_counts) / len(column)
    return bool(most_common_value_rate > sparsity_threshold)


def _find_keys_in_data(keys: list[str], searching_for: list[str]) -> list:
    found = []
    translation = str.maketrans('', '', '_- .')
    to_check = [k.lower().translate(translation) for k in searching_for]
    for k in keys:
        if k.lower().translate(translation) in to_check:
            found.append(k)
    return found
