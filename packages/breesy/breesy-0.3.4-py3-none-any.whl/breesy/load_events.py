import csv
from pathlib import Path

from .Event import Event
from .logging import logger

SUPPORTED_EVENT_EXTENSIONS = ['.tsv', '.csv', '.txt', '.events']

def find_and_load_event_for_file(filename: str, sample_rate: int | float) -> list[Event]:
    """Find and load the event file associated with the EEG data file.

    :param filename: Path to the EEG data file
    :param sample_rate: Sampling rate in Hz

    :return: List of Event objects
    """
    possible_event_files = find_possible_event_files(filename)

    if not possible_event_files:
        return []

    # Load the first found event file
    event_file = possible_event_files[0]

    #TODO: right now we're treating all SUPPORTED_EVENT_EXTENSIONS files as TSV/CSV

    # Load events from the found TSV file
    logger.info(f"Loading events from {event_file}")
    events = load_events_from_csv(event_file, sample_rate)

    return events


def find_possible_event_files(filename: str) -> list[str]:
    """Find all possible event files that might be associated with an EEG data file.

    :param filename: Path to the EEG data file

    :return: List of paths to potential event files
    """
    if not filename:
        return []

    eeg_path = Path(filename)

    # Get the directory and stem parts
    directory = eeg_path.parent.resolve()  # Convert to absolute path
    stem = eeg_path.stem

    # Base patterns without extensions
    base_patterns = [
        # BIDS-style replacement
        stem.replace('_eeg', '_events'),
        # Simple append
        stem + '_events',
        # Simple stem only
        stem,
        # Try removing task part and adding events
        stem.split('_task-')[0] + '_events' if '_task-' in stem else None,
        # Prefix variations
        'events_' + stem,
        # Simple "events" file
        'events'
    ]
    base_patterns = [p for p in base_patterns if p is not None]

    # Create a list of all possible event files to check
    all_possible_event_files = [
        str(directory / (pattern + ext))
        for pattern in base_patterns
        for ext in SUPPORTED_EVENT_EXTENSIONS
    ]
    logger.debug(f"Searching for possible event files: {all_possible_event_files}")
    # Filter the list to include only existing files
    possible_event_files = [event_path for event_path in all_possible_event_files if Path(event_path).exists()]
    logger.debug(f"Found possible event files: {possible_event_files}")

    return possible_event_files

# Note: LLM generated, looks reasonable
def load_events_from_csv(csv_filename: str, sample_rate: int | float) -> list[Event]:
    """Load events from a CSV/TSV file.

    :param csv_filename: Path to the CSV or TSV file containing event data
    :param sample_rate: Sampling rate in Hz for converting time to sample indices

    :return: List of Event objects sorted by sample index
    """

    events = []

    with open(csv_filename, 'r', newline='') as tsvfile:
        # Read the first line to determine the delimiter (TSV or CSV)
        first_line = tsvfile.readline().strip()
        delimiter = '\t' if '\t' in first_line else ','

        # Reset file pointer
        tsvfile.seek(0)

        # Parse header to find relevant columns
        reader = csv.reader(tsvfile, delimiter=delimiter)
        headers = next(reader)

        # Identify relevant columns with flexible naming
        sample_col = None
        onset_col = None
        type_col = None
        value_col = None

        for i, header in enumerate(headers):
            header_lower = header.lower()
            # Sample index column
            if header_lower in ('sample', 'sample_index', 'sampleidx', 'idx', 'index'):
                sample_col = i
            # Onset time column
            elif header_lower in ('onset', 'time', 'timestamp', 'start', 'start_time'):
                onset_col = i
            # Event type column
            elif header_lower in ('type', 'trial_type', 'event_type', 'trial', 'stim_type', 'category'):
                type_col = i
            # Event value column
            elif header_lower in ('value', 'code', 'event_value', 'id', 'trigger'):
                value_col = i

        # Process rows
        for row in reader:
            if not row:  # Skip empty rows
                continue

            try:
                # Try to get sample index directly
                sample_idx = None
                if sample_col is not None and row[sample_col] and row[sample_col].lower() != 'n/a':
                    try:
                        sample_idx = int(float(row[sample_col]))
                    except (ValueError, TypeError):
                        pass

                # If no sample index but we have onset time and sample_rate
                if sample_idx is None and onset_col is not None and sample_rate is not None and row[onset_col] and \
                        row[onset_col].lower() != 'n/a':
                    try:
                        onset_time = float(row[onset_col])
                        sample_idx = int(onset_time/1000 * sample_rate) #TODO: we need to guess whether it's s, ms, or sample index
                    except (ValueError, TypeError):
                        continue

                if sample_idx is None:
                    continue  # Skip if we can't determine the sample index

                # Construct event name
                event_name_parts = []

                if type_col is not None and row[type_col] and row[type_col].lower() != 'n/a':
                    event_name_parts.append(row[type_col])

                if value_col is not None and row[value_col] and row[value_col].lower() != 'n/a':
                    event_name_parts.append(row[value_col])

                event_name = '_'.join(event_name_parts) if event_name_parts else 'event'

                events.append(Event(name=event_name, index=sample_idx))

            except (IndexError, ValueError, TypeError) as e:
                # Skip problematic rows but continue processing
                continue

    return sorted(events, key=lambda event: event.index)
