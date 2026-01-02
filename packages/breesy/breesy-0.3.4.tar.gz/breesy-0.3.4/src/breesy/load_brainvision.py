from pathlib import Path
import numpy as np
import re, unicodedata

# from .Event import Event
from .recording import Recording, RecordingMetadata
from .errors import BreesyError


ERROR_MESSAGE_CONTACT_THE_AUTHORS = 'Contact the authors of the header (.vhdr) file and ask to fix it.'
ERROR_MESSAGE_OPEN_HEADER_IN_NOTEPAD = 'Also, header (.vhdr) files can be opened and inspected with Notepad or other text editor.'


def load_brainvision_eeg(filename: str) -> Recording:
    """Load a BrainVision EEG file.

    :param filename: Path to a BrainVision file, either a header file (.vhdr) or data file (.eeg, .avg, or .seg)

    :return: Recording object containing the loaded data
    """
    file_path = Path(filename)
    if file_path.suffix.lower() in ['.eeg', '.avg', '.seg']:
        vhdr_path = file_path.with_suffix('.vhdr')
        eeg_path = file_path
    elif file_path.suffix.lower() == '.vhdr':
        vhdr_path = file_path
        eeg_path = None

    if not vhdr_path.exists():
        raise BreesyError(
            f"Header file not found for {filename}. Breesy searched for: {vhdr_path}.",
            "BrainVision files require a .vhdr file. Make sure to either provide a correct .vhdr filename, or a filename for a data file with same name and just a different extension."
        )

    metadata = _parse_brainvision_header(vhdr_path)
    if eeg_path is None:
        eeg_path = vhdr_path.parent / metadata['DataFile']
    if not eeg_path.exists():
        raise BreesyError(
            f"Header file references a daat file but it was not found.",
            f"Make sure the data file exists according to the path provided in the header file, which is:\n{metadata['DataFile']}\nUsually, the data file should be in the same directory as the .vhdr file. "
            f'{ERROR_MESSAGE_OPEN_HEADER_IN_NOTEPAD} You can manually change the name of the data file inside it (at your own risk!), using the "DataFile" parameter.'
        )

    data = _read_brainvision_data(eeg_path, metadata)

    # TODO: finish vmrk function
    # vmrk_path = vhdr_path.parent / metadata['MarkerFile']
    # events = _parse_brainvision_markers(vmrk_path, metadata['SamplingInterval'])
    # if not events:
    #     print("No events found in marker file or marker file not present")

    recording_metadata = RecordingMetadata(
        name=vhdr_path.stem,
        file_path=vhdr_path,
        description=f"BrainVision data loaded from {filename}"
    )

    return Recording(
        data=data,
        channel_names=metadata['ch_names'],
        sample_rate=1_000_000 // int(metadata['SamplingInterval']),  # micros to Hz
        # events=events,
        metadata=recording_metadata
    )


def _find_config_parameter_value(config: str, parameter_name: str, mandatory: bool = False) -> str | None:
    values = (x for x in config.split('\n') if x.startswith(parameter_name))
    try:
        value = next(values)
        try:
            next(values)
            raise BreesyError(f'Incorrectly formatted header file: found two values for parameter "{parameter_name}" in same section.',
                              f'{ERROR_MESSAGE_CONTACT_THE_AUTHORS} {ERROR_MESSAGE_OPEN_HEADER_IN_NOTEPAD} '
                              f'If you indeed find more than one mention of parameter "{parameter_name}", you can manually delete one of it (at your own risk!).')
        except StopIteration:
            return value.split(parameter_name+'=')[1]
    except StopIteration:
        if mandatory:
            raise BreesyError(f'Incorrectly formatted header file: mandatory parameter "{parameter_name}" not found.', 
                              f'{ERROR_MESSAGE_CONTACT_THE_AUTHORS} {ERROR_MESSAGE_OPEN_HEADER_IN_NOTEPAD} '
                              f'If you indeed cannot find a row starting with "{parameter_name}", you can manually add that row (at your own risk!).')
        return None


def _get_binary_dtype(binary_format: str):    
    if binary_format == 'INT_16':
        return np.int16
    elif binary_format == 'INT_32':
        return np.int32
    elif binary_format == 'IEEE_FLOAT_32':
        return np.float32
    raise BreesyError(f'Unknown binary format specified: "{binary_format}".',
                      f'{ERROR_MESSAGE_CONTACT_THE_AUTHORS} {ERROR_MESSAGE_OPEN_HEADER_IN_NOTEPAD} '
                       'In the "BinaryFormat" field, BrainVision files only allow "IEEE_FLOAT_32" or "INT_16", and Breesy also allows "INT_32".')


def _reshape_data_by_orientation(raw: np.ndarray, orientation: str, n_channels: int) -> np.ndarray:
    n_samples = len(raw) // n_channels
    if orientation == 'MULTIPLEXED':  # Data is interleaved: Ch1_S1, Ch2_S1, ..., ChN_S1, Ch1_S2, ...
        return raw.reshape((n_samples, n_channels)).T
    elif orientation == 'VECTORIZED':  # Data is by channel: Ch1_S1, Ch1_S2, ..., Ch1_SN, Ch2_S1, ...
        return raw.reshape((n_channels, n_samples))
    raise BreesyError(f'Unknown file orientation specified: "{orientation}".',
                      f'{ERROR_MESSAGE_CONTACT_THE_AUTHORS} {ERROR_MESSAGE_OPEN_HEADER_IN_NOTEPAD} '
                       'In the "DataOrientation" field, BrainVision files only allow "MULTIPLEXED", and Breesy also allows "VECTORIZED".')


def _get_resolutions_according_to_units(scales: list[float], units: list[str]) -> list[float]:
    resolutions = []
    for i, (scale, unit) in enumerate(zip(scales, units)):
        unit_normalized = unit.lower()
        if unit_normalized == 'μv':
            resolutions.append(scale)
        elif unit_normalized == 'mv':
            resolutions.append(scale * 1000)
        elif unit_normalized == 'v':
            resolutions.append(scale * 1_000_000)
        else:
            raise BreesyError(f'Unknown unit specified for channel nr. {i+1}: "{unit}".',
                              f'{ERROR_MESSAGE_CONTACT_THE_AUTHORS} Breesy only supports "μV", "mV", and "V" (not case-sensitive). '
                              f'If you think that "{unit}" unit should also be supported, contact Breesy authors.')
    return resolutions



def _read_brainvision_data(eeg_path: Path, metadata: dict) -> np.ndarray:
    dtype = _get_binary_dtype(binary_format=metadata['BinaryFormat'])   
    with open(eeg_path, 'rb') as f:
        raw_data = np.fromfile(f, dtype=dtype)
    data = _reshape_data_by_orientation(
        raw=raw_data,
        orientation=metadata['DataOrientation'],
        n_channels=int(metadata['NumberOfChannels'])
    )
    resolutions = _get_resolutions_according_to_units(scales=metadata['ch_scales'], units=metadata['ch_units'])
    return data.astype(np.float64) * np.array(resolutions).reshape(-1, 1)


def _parse_brainvision_header(vhdr_path: Path) -> dict:
    # Official specifications: https://www.brainproducts.com/support-resources/brainvision-core-data-format-1-0/
    with open(vhdr_path, 'r', encoding='utf-8') as f:
        config = unicodedata.normalize('NFKC', f.read())
        
    if (
        not (config.startswith("BrainVision Data Exchange Header File Version 1.0") or 
             config.startswith("Brain Vision Data Exchange Header File Version 1.0")) or
        '[Common Infos]' not in config or
        '[Channel Infos]' not in config
    ):
        raise BreesyError(f'Provided file is not valid according to the specification of BrainVision Core Data Format 1.0.',
                          f'Check that the path provided is a correct header file (ending with ".vhdr"):\n{vhdr_path}\n{ERROR_MESSAGE_CONTACT_THE_AUTHORS}')
        
    vhdr = {}
    sections = re.findall(r'(\[.+\]\n[\s\S]+?(?:\n\n|\Z))', config)

    for section in sections:

        if section.startswith('[Common Infos]'):
            for key in ['DataFile', 'DataOrientation', 'NumberOfChannels', 'SamplingInterval']:
                vhdr[key] = _find_config_parameter_value(section, key, mandatory=True)
            for key in ['MarkerFile', 'Averaged']:
                vhdr[key] = _find_config_parameter_value(section, key, mandatory=False)

        elif section.startswith('[Binary Infos]'):
            vhdr['BinaryFormat'] = _find_config_parameter_value(section, 'BinaryFormat', mandatory=True)

        elif section.startswith('[Channel Infos]'):
            vhdr['ch_names'] = []
            vhdr['ch_refs'] = []
            vhdr['ch_scales'] = []
            vhdr['ch_units'] = []
            for row in section.split('\n'):
                if row.startswith(';'):
                    continue
                if row.startswith('Ch'):
                    ch_i, ch_params = row.split('=')
                    expected_ch_name = f"Ch{len(vhdr['ch_names']) + 1}"
                    if ch_i != expected_ch_name:
                        raise BreesyError(f'Channel named "{ch_i}" is given at position which should be channel named "{expected_ch_name}".',
                                          f'Information about some channels is either missed or repeated. {ERROR_MESSAGE_CONTACT_THE_AUTHORS}')

                    ch_params = ch_params.split(',')
                    vhdr['ch_names'].append(ch_params[0])
                    vhdr['ch_refs'].append(ch_params[1])
                    vhdr['ch_scales'].append(float(ch_params[2]))
                    vhdr['ch_units'].append(ch_params[3] if len(ch_params) == 4 else 'μV')
                    
    return vhdr