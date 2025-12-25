"""
Dynamic population sizing strategies for evolution.

Supports gradual population growth or shrinkage during evolution with
multiple interpolation methods for different adaptation curves.

Example usage:
    >>> strategy = PopulationSizeStrategy(
    ...     start_size=20,
    ...     end_size=100,
    ...     method=InterpolationMethod.LINEAR
    ... )
    >>> size_at_gen_25 = strategy.get_size_for_generation(25, max_gen=50)
    >>> # Returns 60 (linearly interpolated midpoint)
"""

from enum import Enum
import math


class InterpolationMethod(str, Enum):
    """Supported interpolation methods for population sizing."""

    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    QUADRATIC = "quadratic"


class PopulationSizeStrategy:
    """
    Strategy for dynamically sizing population during evolution.

    Computes target population size for each generation using interpolation
    from start_size to end_size over the course of evolution.

    Attributes:
        start_size: Initial population size (generation 0)
        end_size: Final population size (max generation)
        method: Interpolation method to use
        align_to: Align sizes to multiples of this value (e.g., 4 for tournament selection)

    Constraints:
        - start_size >= 2 (minimum viable population)
        - end_size >= 2 (minimum viable population)
        - Sizes are always integers (rounded)
        - Monotonic (always increasing or always decreasing)
        - If align_to is set, sizes are multiples of align_to
    """

    MIN_POPULATION_SIZE = 2

    def __init__(
        self,
        start_size: int,
        end_size: int,
        method: InterpolationMethod = InterpolationMethod.LINEAR,
        align_to: int | None = None,
    ):
        """
        Initialize population sizing strategy.

        Args:
            start_size: Initial population size at generation 0
            end_size: Final population size at max generation
            method: Interpolation method (linear, exponential, quadratic)
            align_to: Align all sizes to multiples of this value (e.g., 4 for
                tournament selection). If None, no alignment is performed.

        Raises:
            ValueError: If start_size or end_size < 2, or if align_to < 1
        """
        if start_size < self.MIN_POPULATION_SIZE:
            raise ValueError(f"start_size must be >= {self.MIN_POPULATION_SIZE}, got {start_size}")
        if end_size < self.MIN_POPULATION_SIZE:
            raise ValueError(f"end_size must be >= {self.MIN_POPULATION_SIZE}, got {end_size}")
        if align_to is not None and align_to < 1:
            raise ValueError(f"align_to must be >= 1, got {align_to}")

        self.start_size = start_size
        self.end_size = end_size
        self.method = method
        self.align_to = align_to

    def get_size_for_generation(self, current_gen: int, max_gen: int) -> int:
        """
        Calculate target population size for a given generation.

        Args:
            current_gen: Current generation number (0 to max_gen)
            max_gen: Maximum generation number

        Returns:
            Target population size for current_gen (integer >= 2, aligned if align_to set)

        Example:
            >>> strategy = PopulationSizeStrategy(10, 100, InterpolationMethod.LINEAR)
            >>> strategy.get_size_for_generation(0, 100)
            10
            >>> strategy.get_size_for_generation(50, 100)
            55
            >>> strategy.get_size_for_generation(100, 100)
            100

            >>> strategy = PopulationSizeStrategy(10, 100, align_to=4)
            >>> strategy.get_size_for_generation(50, 100)
            56  # Rounded up to nearest multiple of 4
        """
        if max_gen == 0:
            return self.start_size

        # Normalize generation to [0, 1]
        t = current_gen / max_gen

        # Apply interpolation method
        if self.method == InterpolationMethod.LINEAR:
            size = self._linear_interpolate(t)
        elif self.method == InterpolationMethod.EXPONENTIAL:
            size = self._exponential_interpolate(t)
        elif self.method == InterpolationMethod.QUADRATIC:
            size = self._quadratic_interpolate(t)
        else:
            raise ValueError(f"Unknown interpolation method: {self.method}")

        # Round to integer
        size = int(round(size))

        # Apply alignment if requested
        if self.align_to is not None:
            size = self._align_size(size, self.align_to)

        # Ensure minimum constraint
        size = max(size, self.MIN_POPULATION_SIZE)

        return size

    def _align_size(self, size: int, align_to: int) -> int:
        """
        Align size to nearest multiple of align_to.

        Args:
            size: Unaligned size
            align_to: Alignment factor (e.g., 4)

        Returns:
            Size rounded to nearest multiple of align_to

        Example:
            >>> strategy._align_size(55, 4)
            56  # Rounds up to 56 (next multiple of 4)
            >>> strategy._align_size(56, 4)
            56  # Already aligned
            >>> strategy._align_size(57, 4)
            56  # Rounds down to 56
        """
        # Round to nearest multiple
        return round(size / align_to) * align_to

    def _linear_interpolate(self, t: float) -> float:
        """
        Linear interpolation: size = start + (end - start) * t

        Args:
            t: Normalized time in [0, 1]

        Returns:
            Interpolated size
        """
        return self.start_size + (self.end_size - self.start_size) * t

    def _exponential_interpolate(self, t: float) -> float:
        """
        Exponential interpolation: size = start * (end/start)^t

        Creates accelerating growth (or deceleration for shrink).
        Most change happens near the end.

        Args:
            t: Normalized time in [0, 1]

        Returns:
            Interpolated size
        """
        if self.start_size == self.end_size:
            return self.start_size

        # Compute ratio
        ratio = self.end_size / self.start_size

        # Exponential interpolation: start * ratio^t
        return self.start_size * (ratio**t)

    def _quadratic_interpolate(self, t: float) -> float:
        """
        Quadratic interpolation: size = start + (end - start) * t^2

        Creates smooth acceleration (slower at start, faster at end).
        Curve is between linear and exponential.

        Args:
            t: Normalized time in [0, 1]

        Returns:
            Interpolated size
        """
        return self.start_size + (self.end_size - self.start_size) * (t**2)

    def __repr__(self) -> str:
        align_str = f", align_to={self.align_to}" if self.align_to else ""
        return (
            f"PopulationSizeStrategy("
            f"start={self.start_size}, "
            f"end={self.end_size}, "
            f"method={self.method.value}"
            f"{align_str})"
        )
