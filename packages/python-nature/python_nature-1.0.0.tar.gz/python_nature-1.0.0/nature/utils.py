import os
import re
import subprocess as sp

import numpy as np

from datetime import datetime
from typing import Any, Callable, Generator, Iterable, Iterator, Sequence, cast
from numpy.typing import NDArray
from pandas import DataFrame
from tabulate import tabulate


RE_SNAKE = re.compile(r"([a-z0-9])([A-Z])")


def is_debug():
    return bool(os.environ.get("NATURE_DEBUG"))


def builtin_id(obj: object) -> int:
    return id(obj)


def clamp(x: float | int, x_min: float | int, x_max: float | int) -> float:
    return min(x_max, max(x_min, x))


def flatten(seq: Any | Iterable[Any | Sequence[Any]] | tuple[Any, ...]) -> list[Any]:
    if not np.iterable(seq) or isinstance(seq, str):
        return [seq]
    result = []
    for item in seq:
        if isinstance(item, Sequence) and not isinstance(item, (str, bytes)):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result


def is_scalar(value: Any) -> bool:
    return isinstance(value, (float, int, complex, bool))


def drop_initial_nans(df: DataFrame) -> DataFrame:
    first_valid = df.notna().all(axis=1).idxmax()
    return df.loc[first_valid:]


def bounded_exponential(lambd: float = 1.0) -> float:
    """
    Generate a value in [0, 1] from an exponential distribution.

    Args:
        lambd (float): Rate parameter (higher = steeper decay).

    Returns:
        float: A number in [0,1] following an exponential decay.
    """
    x = np.random.exponential(scale=1 / lambd)  # Generate exponential sample
    return 1 - np.exp(-lambd * x)  # Transform into [0,1] range


def proximity_score(x: float, target: float) -> float:
    if not target:
        return abs(1 - x)
    return 1 - abs(x - target) / target


def random_subsequences(
    df: DataFrame,
    size: int,
    count: int,
    random_state: int | None = None,
):
    max_slices = min(count, len(df) // size)
    indices = np.arange(max_slices)
    rng = np.random.default_rng(random_state)
    rng.shuffle(indices)
    return [df.iloc[i * size : (i + 1) * size] for i in indices]


def iter_batches(
    values: Sequence | NDArray, size: int
) -> Generator[NDArray | Sequence[Sequence], None, None]:
    return (values[i : i + size] for i in range(0, len(values), size))


def iter_batches_slices(
    values: Sequence | NDArray, size: int
) -> Generator[slice | Sequence[slice], None, None]:
    return (slice(i, min(i + size, len(values))) for i in range(0, len(values), size))


def runtime_stats(
    target: Callable, rounds: int = 1, title: str | None = None, verbose=True
) -> tuple[float, float]:
    deltas = []

    for _ in range(rounds):
        t1 = datetime.now()
        target()
        t2 = datetime.now()
        deltas.append((t2 - t1).total_seconds())

    deltas = np.array(deltas)

    total = float(np.sum(deltas, dtype=float))
    mean = float(np.mean(deltas, dtype=float))
    std = float(np.std(deltas, dtype=float))

    if verbose:
        print(
            f'{title+ " " if title else ""}Runtime (seconds)\n',
            tabulate(
                [
                    ("rounds", rounds),
                    ("mean", str(round(mean, 4))),
                    ("std", str(round(std, 4))),
                    ("total", str(round(total, 4))),
                    ("rounds/sec", str(round(rounds / total, 4))),
                ]
            ),
        )

    return (total, mean)


def to_snake_case(text: str) -> str:
    text = RE_SNAKE.sub(r"\1_\2", text)
    return text.lower()


def get_git_info() -> tuple[str, str]:
    """Returns (branch_name, commit_hash)."""
    try:
        branch = sp.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True).strip()
        commit = sp.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        return branch, commit
    except Exception:
        return "unknown", "unknown"
