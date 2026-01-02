from urllib.request import urlopen, Request
import certifi, ssl
from shutil import copyfileobj
from pathlib import Path
from tqdm.auto import tqdm

from .errors import BreesyError
from .logging import logger


AVAILABLE_DATAFILES = ['alpha', 'pangolin']


def download_example_data(dataset_name: str, dir_name: str = "tmp", ssl_context=None) -> str:
    f"""Download example EEG file for testing and learning.

    Downloads publicly available EEG data files. Currently available files include: {AVAILABLE_DATAFILES}.

    :param dataset_name: Name of the file to load
    :param dir_name: Directory to save downloaded file (will be created if does not exist)
    :param ssl_context: SSL context for secure downloads

    :return: path to the downloaded file
    """

    # TODO: some downloads take time, do some loading bar?
    # TODO: add urls for more information about each dataset
    if dataset_name == "alpha":
        filename = "subject_01.mat"
        url = "https://zenodo.org/records/2348892/files/subject_01.mat?download=1"
        # ch_names = ["Fp1", "Fp2", "FC5", "FC6", "Fz", "T7", "Cz", "T8",
        #             "P7", "P3", "Pz", "P4", "P8", "O1", "Oz", "O2"]
        # sample_rate = 512
    
    # elif dataset_name == "madhd":
    #     filename = "MADHD.mat"
    #     url = "https://data.mendeley.com/public-files/datasets/6k4g25fhzg/files/9c5928cf-f8ef-485b-ac5b-f17b2df935f3/file_downloaded"
    #     # ch_names = ["Cz", "F4"]
    #     # sample_rate = 256

    elif dataset_name == "pangolin":
        filename = "S1_run8.mat"
        url = "https://osf.io/download/jrcn8/?view_only=d23acfd50655427fbaae381a17cbfbcc"
        # ch_names = [f"ch{i+1}" for i in range(258)]  # this dataset has no standard channel names
        # sample_rate = 600

    # elif dataset_name == "schalk":
    #     filename = "S001R01.edf"
    #     url = "https://www.physionet.org/files/eegmmidb/1.0.0/S001/S001R01.edf?download"
    #     ch_names = ['Fc5', 'Fc3', 'Fc1', 'Fcz', 'Fc2', 'Fc4', 'Fc6',
    #                 'C5', 'C3', 'C1', 'Cz', 'C2', 'C4', 'C6',
    #                 'Cp5', 'Cp3', 'Cp1', 'Cpz', 'Cp2', 'Cp4', 'Cp6',
    #                 'Fp1', 'Fpz', 'Fp2', 'Af7', 'Af3', 'Afz', 'Af4', 'Af8',
    #                 'F7', 'F5', 'F3', 'F1', 'Fz', 'F2', 'F4', 'F6', 'F8',
    #                 'Ft7', 'Ft8', 'T7', 'T8', 'T9', 'T10', 'Tp7', 'Tp8',
    #                 'P7', 'P5', 'P3', 'P1', 'Pz', 'P2', 'P4', 'P6', 'P8',
    #                 'Po7', 'Po3', 'Poz', 'Po4', 'Po8', 'O1', 'Oz', 'O2', 'Iz'
    #                 ]
    #     sample_rate = 160

    # elif dataset_name == "telemetry":
    #     filename = "ST7011J0-PSG.edf"
    #     url = "https://www.physionet.org/files/sleep-edfx/1.0.0/sleep-telemetry/ST7011J0-PSG.edf?download"
    #     ch_names = range(5)  # TODO: get actual channel names
    #     sample_rate = 100

    else:
        available_string = ", ".join([f'"{n}"' for n in AVAILABLE_DATAFILES])
        raise BreesyError(f'Unknown name of filename provided: "{dataset_name}".', 
                          f'Please use one of available names ({available_string}).')   

    dirpath = Path(dir_name)
    dirpath.mkdir(parents=True, exist_ok=True)
    filepath = dirpath / filename

    if not filepath.exists():
        logger.info(f'Will download the data file from {url}')
        if ssl_context is None:
            ssl_context = ssl.create_default_context(cafile=certifi.where())
        req = Request(url, headers={'User-Agent' : "Magic Browser"})
        with urlopen(req, context=ssl_context) as in_stream:
            file_size = int(in_stream.headers.get('Content-Length', 0))
            with tqdm.wrapattr(in_stream, "read", total=file_size,
                              desc=f"Downloading {filename}",
                              unit='B', unit_scale=True, unit_divisor=1024) as wrapped_stream:
                with open(filepath, 'wb') as out_file:
                    copyfileobj(wrapped_stream, out_file)
        logger.info(f'Done! File saved in: {filepath}')
    else:
        logger.info(f'File already exists: {filepath}')

    return filepath
