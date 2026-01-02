"""Breesy - Brainwave Retrieval, Extraction, and Easy Signal Yield.

Breesy provides easy-to-use functions and pipelines for neuroscience students
who want to apply signal processing and statistical methods on EEG data.
"""

__version__ = '0.3.4'

# Import core classes
from .recording import Recording
from .Event import Event
from .RecordingMetadata import RecordingMetadata

# Make key modules and functions available at package level
from . import constants, events, features, errors, filtering, \
    load, load_events, playground, plots, processing, recording, type_hints, logging
