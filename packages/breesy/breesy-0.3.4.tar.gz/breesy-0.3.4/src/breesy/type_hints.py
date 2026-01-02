from functools import wraps
from typing import get_type_hints

import numpy as np

IS_ENABLED = True

# Simple types with basic examples
simple_type_examples = {
    str: '"hello world"',
    int: "42",
    float: "3.14, 10., or 1.0",
    bool: "True"
}

# Complex types with detailed guidance
complex_type_help = {
    np.ndarray: {
        'example': 'np.array([1.2, -0.5, 0.8])',
        'guidance': ('You can create an ndarray from a list using np.array(your_list), '
                     'or load data from a file using np.loadtxt() or np.genfromtxt(). '
                     'Common EEG data shape is (channels, samples)')
    },
    np.float64: {
        'example': '0.0',
        'guidance': 'Convert using float(value) or np.float64(value)'
    },
    np.int64: {
        'example': '128',
        'guidance': 'Convert using int(value) or np.int64(value)'
    },
    # Circular dependency, so we can't import Recording here
    # Recording: {
    #     'example': 'Recording(data=np.array([1.2, -0.5, 0.8]), sample_rate=250, channel_names=["F3", "F4"])',
    #     'guidance': 'Create a Recording object with data, sample_rate, and channel_names'
    # }
}


class TypeHintError(Exception):
    def __init__(self, expected_type: type, received_type: type, arg_name: str):
        message = f"Argument '{arg_name}' should be {expected_type.__name__}, but you provided a {received_type.__name__}"
        super().__init__(message)

        if expected_type in simple_type_examples:
            example = simple_type_examples[expected_type]
            self.suggested_fix = f"Try using a value of type {expected_type.__name__} like {example}"
            return

        if expected_type in complex_type_help:
            help_info = complex_type_help[expected_type]
            self.suggested_fix = (f"Create a {expected_type.__name__} using {help_info['example']}. "
                                  f"{help_info['guidance']}")
            return

        self.suggested_fix = "The type you need seems rare, so ask your lecturer for advice!"

    def __str__(self):
        if self.suggested_fix:
            return f"\n ⚠️ {super().__str__()}. \n 💡 SUGGESTED FIX: {self.suggested_fix}"
        return f"\n ⚠️ {super().__str__()}"


def enforce_type_hints(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        hints = get_type_hints(func)
        sig = func.__code__.co_varnames[:func.__code__.co_argcount]

        for arg_name, arg_value in zip(sig, args):
            if arg_name in hints:
                expected_type = hints[arg_name]
                # Get the raw type without generics
                if hasattr(expected_type, "__origin__"):
                    continue  # Skip generic types

                try:
                    if not isinstance(arg_value, expected_type):
                        raise TypeHintError(expected_type, type(arg_value), arg_name)
                except TypeError:  # isinstance() fails with generic types
                    continue  # Skip this check

        return func(*args, **kwargs)

    return wrapper