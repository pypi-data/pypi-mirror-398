# Breesy

Easy EEG analysis for neuroscience.

## Installation
```bash
pip install breesy
```

## Quick Start  
```python
import breesy

# Load EEG data
recording = breesy.load.load_dataset("your_data.mat")

# Basic preprocessing  
clean = breesy.processing.mean_centering(recording)
filtered = breesy.processing.remove_powerline_noise(clean)

# Visualize
breesy.plots.plot_recording(filtered)
```

## Features
- Load various EEG file formats
- Simple preprocessing and filtering
- Clear error messages with suggestions

## Dependencies
- Numpy
- Matplotlib
- Scipy
- Scikit-learn
- tqdm