__all__ = ("Seed", "get_rng", "coinflip", "draw", "shuffle", "integers", "signed_max")

import random
from collections.abc import Iterator, Sequence
from numbers import Integral
from typing import TypeAlias, TypeVar

T = TypeVar("T")
Seed: TypeAlias = int | random.Random | None


def get_rng(seed: Seed = None) -> random.Random:
    """Return a random.Random instance from the given seed."""
    if isinstance(seed, random.Random):
        return seed
    elif seed is None or isinstance(seed, int):
        return random.Random(seed)
    else:
        raise ValueError(f"invalid {seed=!r}")


def coinflip(bias: float, seed: Seed = None) -> bool:
    """Return outcome of a simulated random coin flip with a specified bias."""
    if not (0 <= bias <= 1):
        raise ValueError(f"invalid {bias=!r}; expected 0 <= bias <= 1")
    rng = get_rng(seed)
    return rng.random() < bias


def draw(items: Sequence[T], replace: bool, size: int, seed: Seed = None) -> list[T]:
    """Return a new list of items randomly drawn from the input sequence."""
    rng = get_rng(seed)
    if size < 0:
        raise ValueError(f"invalid {size=!r}; expected >= 0")
    if not items or size == 0:
        return []
    if replace:
        return rng.choices(items, k=size)
    return rng.sample(items, k=size)


def shuffle(items: list[T], seed: Seed = None) -> list[T]:
    """Return a randomly shuffled copy of the input sequence."""
    return draw(items, replace=False, size=len(items), seed=seed)


def integers(size: int, lower: int, upper: int, seed: Seed = None) -> Iterator[int]:
    """Return random integers between lower (inclusive) and upper (exclusive)."""
    rng = get_rng(seed)
    return (rng.randrange(lower, upper) for _ in range(size))


def signed_max(bit_width: int, /) -> int:
    """Return the maximum signed integer representable for the given bit width."""
    if isinstance(bit_width, bool) or not isinstance(bit_width, Integral):
        raise TypeError(f"unsupported type {type(bit_width).__name__!r}; expected int")

    bit_width = int(bit_width)
    if bit_width < 2:
        raise ValueError(f"invalid value {bit_width!r}; expected >= 2")

    return (1 << (bit_width - 1)) - 1
