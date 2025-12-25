import math
import random
import numpy as np

from collections import deque
from typing import Any, Iterable, Sequence, cast


from pandas import DataFrame, Series

# Default seeds for reproducible random number generation
# Users can customize this list for their own reproducibility needs
SEEDS = list(range(1, 1001))

seed_buff = deque(SEEDS)


class Random(random.Random):
    np_shuffle = np.random.shuffle
    np_choice = np.random.choice
    np_exponential = np.random.exponential

    def __init__(self, x: int | float | str | bytes | bytearray | None = None) -> None:
        super().__init__(x or (seed_buff.popleft() if seed_buff else np.random.randint(0, 2**32)))

    def flip(self, p: float = 0.5):
        return self.random() < p

    def column(self, df: DataFrame, dtype: type | Iterable[type]) -> Series | None:
        filtered_df_cols = df.select_dtypes(include=cast(Any, dtype)).columns
        return df[self.choice(filtered_df_cols)] if len(filtered_df_cols) > 0 else None

    def sample_folds(
        self,
        df: DataFrame,
        size: int,
        count: int,
        random_state: int | None = None,
    ):
        max_slices = max(1, len(df) // size)
        indices = np.arange(max_slices - 1)
        rng = np.random.default_rng(random_state or self.randint(1, (1 << 32) - 1))
        rng.shuffle(indices)
        return [df.iloc[i : i + size] for i in indices[:count]]

    def sample_folds_indices_and_size(
        self,
        df: DataFrame,
        size: int,
        count: int,
        random_state: int | None = None,
    ) -> tuple[np.ndarray, int]:
        max_slices = max(1, len(df) // size)
        indices = np.arange(max_slices - 1)
        rng = np.random.default_rng(random_state or self.randint(1, (1 << 32) - 1))
        rng.shuffle(indices)
        return (indices[:count], size)

    def log_uniform(self, a: float, b: float) -> float:
        """Sample a value from a log-uniform distribution between a and b.

        If a == 0, it's treated as a very small positive number.
        """
        if b <= 0:
            raise ValueError("b must be > 0 for log-uniform sampling")
        if a < 0:
            raise ValueError("a must be >= 0 for log-uniform sampling")

        a = max(a, 1e-10)  # Prevent log(0)
        return math.exp(random.uniform(math.log(a), math.log(b)))

    def decay(self, lower: float, upper: float, rate: float = 5.0) -> float:
        """
        Return a random integer in [lower, upper], biased exponentially toward lower.

        - lower: minimum value (inclusive)
        - upper: maximum value (inclusive)
        - rate: exponential steepness (> 0); higher = stronger bias toward lower
        """

        if lower > upper:
            raise ValueError("lower must be <= upper")
        if rate <= 0:
            raise ValueError("rate must be > 0")

        u = np.random.random()  # in [0, 1)
        # Invert the exponential bias to favor lower values
        x = np.exp(-rate * u)
        x = (x - np.exp(-rate)) / (1 - np.exp(-rate))  # normalize to [0, 1]

        # Scale to [lower, upper]
        val = int(lower + x * (upper - lower + 1))
        return min(val, upper)
