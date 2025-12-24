from .core import normWindow, transformTS, distanceCalculation, getRandomCOP
from .optimisation import optimiseRandom as optimiseRandom
from .tests import testingRandomness, testingIrreversibility
from .reservoir_computing import testingReservoirComputing


__version__ = "0.3.0"

__all__ = [
    "__version__",
    "normWindow",
    "transformTS",
    "distanceCalculation",
    "getRandomCOP",

    "optimiseRandom",

    "testingRandomness",
    "testingIrreversibility",
    "testingReservoirComputing",
]

