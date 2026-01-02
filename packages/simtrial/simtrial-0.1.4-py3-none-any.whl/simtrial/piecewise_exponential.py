"""
Tools for working with the piecewise exponential distribution.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import cast

import numpy as np
from numpy.typing import NDArray

_RANDOM_STATE: np.random.Generator | None = None


def _default_rng() -> np.random.Generator:
    """
    Return a module-level random number generator.

    Returns:
        The reusable random number generator for piecewise exponential sampling.
    """

    global _RANDOM_STATE
    if _RANDOM_STATE is None:
        _reset_rng()
    return cast(np.random.Generator, _RANDOM_STATE)


def _reset_rng(seed: int | None = None) -> None:
    """
    Initialize the module-level random number generator.

    Args:
        seed: Seed used to reset the generator.

    Returns:
        Nothing.
    """

    global _RANDOM_STATE
    _RANDOM_STATE = np.random.default_rng(seed)


def set_random_seed(seed: int) -> None:
    """
    Set the seed for the module-level random number generator.

    Args:
        seed: Seed value that controls reproducibility.

    Returns:
        Nothing.
    """

    _reset_rng(seed=seed)


@dataclass
class PiecewiseExponential:
    """
    Piecewise exponential sampler based on the inverse cumulative distribution.

    Args:
        durations: Interval durations for each hazard rate segment; all but the
            final duration must be finite and strictly positive, while the last
            entry may be set to ``math.inf`` to represent an open-ended tail.
        rates: Hazard rates aligned with the provided durations.
        rng: Optional random number generator.

    Raises:
        ValueError: Raised when inputs are invalid.
    """

    durations: Sequence[float]
    rates: Sequence[float]
    rng: np.random.Generator | None = None

    def __post_init__(self) -> None:
        """
        Validate inputs and precompute cumulative quantities.

        Returns:
            Nothing.
        """

        self._durations = np.asarray(self.durations, dtype=float)
        self._rates = np.asarray(self.rates, dtype=float)

        if self._durations.ndim != 1:
            raise ValueError("durations must be one-dimensional")
        if self._rates.ndim != 1:
            raise ValueError("rates must be one-dimensional")
        if self._durations.size == 0:
            raise ValueError("durations must contain at least one interval")
        if self._durations.size != self._rates.size:
            raise ValueError("durations and rates must have the same length")
        if not np.all(np.isfinite(self._durations[:-1])):
            raise ValueError(
                "durations must be finite except possibly the last interval, "
                "which may extend to infinity"
            )
        if np.any(self._durations[:-1] <= 0):
            raise ValueError("durations before the final interval must be positive")
        last_duration = float(self._durations[-1])
        if math.isnan(last_duration):
            raise ValueError("final duration must be finite or math.inf")
        if last_duration <= 0:
            raise ValueError("final duration must be positive")
        if np.any(~np.isfinite(self._rates)):
            raise ValueError("rates must be finite")
        if np.any(self._rates <= 0):
            raise ValueError("rates must be strictly positive")

        self._cum_time = np.concatenate(
            (np.array([0.0]), np.cumsum(self._durations[:-1]))
        )
        self._cum_hazard = np.concatenate(
            (np.array([0.0]), np.cumsum(self._durations[:-1] * self._rates[:-1]))
        )

    def sample(
        self,
        size: int | tuple[int, ...] | None = None,
        rng: np.random.Generator | None = None,
    ) -> float | NDArray[np.float64]:
        """
        Draw samples using the inverse cumulative distribution function.

        Args:
            size: Requested sample size or shape.
            rng: Optional random number generator overriding the stored generator.

        Returns:
            A scalar when `size` is `None`, otherwise an array of samples.
        """

        generator = rng or self.rng or _default_rng()

        if size is None:
            uniform = float(generator.uniform())
            hazard = -math.log(uniform)
            index = int(np.searchsorted(self._cum_hazard, hazard, side="right") - 1)
            base_time = float(self._cum_time[index])
            return base_time + (hazard - float(self._cum_hazard[index])) / float(
                self._rates[index]
            )

        uniforms = generator.uniform(size=size)
        hazards = -np.log(uniforms)
        indices = np.searchsorted(self._cum_hazard, hazards, side="right") - 1
        base_times = self._cum_time[indices]
        return base_times + (hazards - self._cum_hazard[indices]) / self._rates[indices]
