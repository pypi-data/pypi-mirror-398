from typing import Any, Sequence

import numpy as np


class RingBuffer(Sequence):
    def __init__(self, capacity: int, dtype: type = object):
        self.capacity = capacity
        self.buffer = np.empty(capacity, dtype=dtype)
        self.size = 0
        self.idx = 0

    def append(self, value: Any):
        self.buffer[self.idx] = value
        self.idx = (self.idx + 1) % self.capacity
        if self.size < self.capacity:
            self.size += 1

    def extend(self, values):
        for value in values:
            self.append(value)

    def clear(self):
        self.buffer[:] = None
        self.size = 0
        self.idx = 0

    def to_array(self):
        return (
            self.buffer[: self.size]
            if self.size < self.capacity
            else np.roll(self.buffer, -self.idx)[: self.size]
        )

    def __len__(self):
        return self.size

    def __getitem__(self, idx: Any) -> Any:
        if isinstance(idx, slice):
            return [self[i] for i in range(*idx.indices(self.size))]
        if idx < 0:
            idx += self.size
        if not 0 <= idx < self.size:
            raise IndexError("Index out of range")
        return self.buffer[(self.idx - self.size + idx) % self.capacity]

    def __iter__(self):
        return (self[i] for i in range(self.size))
