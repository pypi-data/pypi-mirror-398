"""
teorver — учебная библиотека по комбинаторике и теории вероятностей
"""

from .combinatorics import *
from .probability import *

__version__ = "0.0.1"
__author__ = "Амина"

__all__ = [
    # Из combinatorics
    "factorial",
    "permutations",
    "arrangements",
    "combinations",
    "arrangements_with_repetition",
    "combinations_with_repetition",

    # Из probability
    "classical_probability",
    "bernoulli_probability",
    "expected_value",
    "total_probability",
    "bayes_probability",
]