from breesy.load import load_recording
from breesy.plots import plot_recording
from breesy.errors import BreesyError

raise BreesyError(
    "No info found about sample rate.",
    "Please find the recording's sample rate in data description and set manually by "
    "passing an additional parameter 'sample_rate' into the data loading function. "
    "Example: load_recording(path, sample_rate=128)."
)
