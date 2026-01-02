from breesy.case_insensitive_dict import CaseInsensitiveDict

"""Standard EEG frequency bands in Hz.

Dictionary mapping band names to frequency ranges (low, high) in Hz.
"""
CLASSIC_BANDWIDTHS: dict[str, tuple[float | int, float | int]] = {
    'delta': (1, 4),
    'theta': (4, 8),
    'alpha': (8, 13),
    'beta': (13, 30),
    'gamma': (30, 45),
    'high_gamma': (45, 100)
}

"""Common EEG electrode montages/systems.

Dictionary mapping montage names to dictionaries of electrode names and coordinates on a head with r=1.
"""
EEG_MONTAGES = {
    # International 10-20 system
    '10-20': CaseInsensitiveDict[str, tuple[float, float]](data = {
        'Fp1': (-0.24721, 0.76085),
        'Fp2': (0.24721, 0.76085), 
        'F7': (-0.64721, 0.47023),
        'F3': (-0.32551, 0.41761),
        'Fz': (0.00000, 0.40000),
        'F4': (0.32551, 0.41761),
        'F8': (0.64721, 0.47023),
        'T7': (-0.80000, 0.00000),
        'C3': (-0.40000, 0.00000),
        'Cz': (0.00000, 0.00000),
        'C4': (0.40000, 0.00000),
        'T8': (0.80000, 0.00000),
        'P7': (-0.64721, -0.47023),
        'P3': (-0.32551, -0.41761),
        'Pz': (0.00000, -0.40000),
        'P4': (0.32551, -0.41761),
        'P8': (0.64721, -0.47023),
        'O1': (-0.24721, -0.76085),
        'O2': (0.24721, -0.76085),
        'A1': (-1.15000, 0.00000),
        'A2': (1.15000, 0.00000),
    }),

    # Extended 10-10 system
    '10-10': CaseInsensitiveDict[str, tuple[float, float]](data = {
        'FC8': (0.76085, 0.24721),
        'F8': (0.64721, 0.47023),
        'AF8': (0.47023, 0.64721),
        'Fp2': (0.24721, 0.76085),
        'Fpz': (0.0, 0.8),
        'Fp1': (-0.24721, 0.76085),
        'AF7': (-0.47023, 0.64721),
        'F7': (-0.64721, 0.47023),
        'FC7': (-0.76085, 0.24721),
        'P7': (-0.64721, -0.47023),
        'PO7': (-0.47023, -0.64721),
        'O1': (-0.24721, -0.76085),
        'Oz': (0.0, -0.8),
        'O2': (0.24721, -0.76085),
        'PO8': (0.47023, -0.64721),
        'P8': (0.64721, -0.47023),
        'AFz': (0.0, 0.6),
        'Fz': (0.0, 0.4),
        'FCz': (0.0, 0.2),
        'Cz': (0.0, 0.0),
        'CPz': (0.0, -0.2),
        'Pz': (0.0, -0.4),
        'POz': (0.0, -0.6),
        'T10': (1.0, 0.0),
        'FT10': (0.95106, 0.30902),
        'F10': (0.80902, 0.58779),
        'Nz': (0.0, 1.0),
        'F9': (-0.80902, 0.58779),
        'FT9': (-0.95106, 0.30902),
        'T9': (-1.0, 0.0),
        'TP9': (-0.95106, -0.30902),
        'P9': (-0.80902, -0.58779),
        'Iz': (-0.0, -1.0),
        'P10': (0.80902, -0.58779),
        'TP10': (0.95106, -0.30902),
        'F5': (-0.48707, 0.43957),
        'F3': (-0.32551, 0.41761),
        'F1': (-0.16299, 0.40441),
        'F2': (0.16299, 0.40441),
        'F4': (0.32551, 0.41761),
        'F6': (0.48707, 0.43957),
        'FC5': (-0.57127, 0.22657),
        'FC3': (-0.38115, 0.21181),
        'FC1': (-0.19067, 0.20295),
        'FC2': (0.19067, 0.20295),
        'FC4': (0.38115, 0.21181),
        'FC6': (0.57127, 0.22657),
        'C5': (-0.6, 0.0),
        'C3': (-0.4, 0.0),
        'C1': (-0.2, 0.0),
        'C2': (0.2, 0.0),
        'C4': (0.4, 0.0),
        'C6': (0.6, 0.0),
        'CP5': (-0.57127, -0.22657),
        'CP3': (-0.38115, -0.21181),
        'CP1': (-0.19067, -0.20295),
        'CP2': (0.19067, -0.20295),
        'CP4': (0.38115, -0.21181),
        'CP6': (0.57127, -0.22657),
        'P5': (-0.48707, -0.43957),
        'P3': (-0.32551, -0.41761),
        'P1': (-0.16299, -0.40441),
        'P2': (0.16299, -0.40441),
        'P4': (0.32551, -0.41761),
        'P6': (0.48707, -0.43957),
        'AF3': (-0.23511, 0.6),
        'AF4': (0.23511, 0.6),
        'PO3': (-0.23511, -0.6),
        'PO4': (0.23511, -0.6),
        'A1': (-1.15, 0.0),
        'A2': (1.15, 0.0),
        'T7': (-0.8, 0.0),
        'T8': (0.8, 0.0),
        'TP7': (-0.76085, -0.24721),
        'TP8': (0.76085, -0.24721),
    }),
}

# Numeric thresholds
POWERLINE_POWER_THRESHOLD = 1.1
DEAD_CHANNEL_SD_THRESHOLD = 0.1
NOISY_CHANNEL_VARIANCE_THRESHOLD = 10.0

# Filter orders
POWERLINE_NOTCH_QUALITY_FACTOR = 30
BUTTER_FILTER_ORDER = 5

# Frequencies
BASELINE_FOR_PEAKS_LOW = 20
BASELINE_FOR_PEAKS_HIGH = 40
SLOWDRIFT_REMOVAL_FREQ = 0.1

# Plotting constants
COLOR_SPECTRUM = '#aa0000'
TOPOGRAPHY_GRID_RESOLUTION = 500
TOPOGRAPHY_CONTOUR_LEVELS = 14
TOPOGRAPHY_CONTOUR_COLOR = "#000000"
TOPOGRAPHY_CONTOUR_ALPHA = 0.4
TOPOGRAPHY_CONTOUR_WIDTH = 0.5
TOPOGRAPHY_ELECTRODE_COLOR = "#000000"
TOPOGRAPHY_ELECTRODE_SIZE = 25
COLOR_HEAD_FILL = "#ffffff"
COLOR_HEAD_EDGE = "#000000"
COLOR_ELECTRODE = "#7eff34"
COLOR_HIGHLIGHT_ELECTRODE = "#ff7e2e"

# Playground
PLAYGROUND_WAVE_SAMPLE_RATE = 1000  # Hz
PLAYGROUND_WAVE_DURATION = 1  # s
PLAYGROUND_Y_ROUND_FACTOR = 8