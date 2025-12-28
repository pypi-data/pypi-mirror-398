__all__ = (
    "__version__",
    "Seed",
    "coinflip",
    "draw",
    "get_rng",
    "integers",
    "shuffle",
    "signed_max",
)

from importlib import metadata

from purechance.core import Seed, coinflip, draw, get_rng, integers, shuffle, signed_max

__version__ = metadata.version(__name__)
