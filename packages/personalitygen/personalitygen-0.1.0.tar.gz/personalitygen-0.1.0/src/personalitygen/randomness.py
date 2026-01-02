"""Random utilities used by personalitygen."""

from __future__ import annotations

import random
import statistics
from typing import Protocol


class RandomSource(Protocol):
    """Minimal interface needed for deterministic sampling."""

    def gauss(self, mu: float, sigma: float) -> float: ...

    def uniform(self, a: float, b: float) -> float: ...


def _coerce_rng(rng: RandomSource | None) -> RandomSource:
    return rng if rng is not None else random


def random_gaussian(
    *,
    mean: float,
    stddev: float,
    min_value: float,
    max_value: float,
    rng: RandomSource | None = None,
) -> float:
    """Draw a truncated Gaussian sample within the provided bounds."""
    if stddev <= 0:
        raise ValueError("stddev must be positive")
    if min_value > max_value:
        raise ValueError("min_value must be <= max_value")

    source = _coerce_rng(rng)
    distribution = statistics.NormalDist(mean, stddev)
    lower = distribution.cdf(min_value)
    upper = distribution.cdf(max_value)
    if lower >= upper:
        return max(min_value, min(max_value, mean))

    cdf_epsilon = 1e-12
    lower = max(lower, cdf_epsilon)
    upper = min(upper, 1.0 - cdf_epsilon)
    if lower >= upper:
        return max(min_value, min(max_value, mean))

    u = source.uniform(lower, upper)
    return distribution.inv_cdf(u)
