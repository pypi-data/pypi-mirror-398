from typing import Iterator, Sequence, cast, overload

import numpy as np

from nature.species import Species
from nature.typing import SpeciesArray


class NativeHallOfFame:
    """Native Hall of Fame for tracking elite individuals.

    Maintains a sorted collection of the best individuals seen during evolution.
    Uses lexicographic ordering based on fitness values (best first).

    Attributes:
        maxsize: Maximum number of individuals to maintain
        items: List of elite Species instances (sorted by fitness, descending)

    Example:
        >>> hof = NativeHallOfFame(maxsize=3)
        >>> hof.update(population)  # Add best individuals from population
        >>> best = hof.best  # Get the best individual
        >>> len(hof)  # Number of elites stored
    """

    def __init__(self, maxsize: int):
        """Initialize Hall of Fame with capacity.

        Args:
            maxsize: Maximum number of individuals to store
        """
        self.maxsize = maxsize
        self._items: list[Species] = []

    def update(self, population: SpeciesArray | Sequence[Species]) -> None:
        """Update hall of fame with best individuals from population.

        Maintains sorted order (best fitness first) and respects maxsize capacity.
        Individuals are compared using their fitness values.

        Args:
            population: Array or sequence of Species instances
        """
        # Convert to list for easier handling
        if isinstance(population, np.ndarray):
            pop_list = population.tolist()
        else:
            pop_list = list(population)

        # Filter out individuals without valid fitness
        valid_pop = [ind for ind in pop_list if ind.fitness.valid]  # type: ignore

        if not valid_pop:
            return

        # Merge hall of fame with new population
        combined = self._items + valid_pop

        # Sort by fitness (descending - best first)
        # Use negative comparison to get descending order
        combined.sort(key=lambda ind: ind.fitness, reverse=True)

        # Keep only the best maxsize individuals
        self._items = combined[: self.maxsize]

    def insert(self, item: Species) -> None:
        """Insert a single individual into hall of fame.

        Maintains sorted order and capacity constraints.

        Args:
            item: Species instance to insert
        """
        if not item.fitness.valid:
            return

        # Insert in sorted position (reverse order for descending sort)
        # We want best (highest) fitness first
        insert_index = 0
        for i, existing in enumerate(self._items):
            if item.fitness <= existing.fitness:
                insert_index = i + 1
            else:
                break

        self._items.insert(insert_index, item)

        # Maintain capacity
        if len(self._items) > self.maxsize:
            self._items = self._items[: self.maxsize]

    def clear(self) -> None:
        """Remove all individuals from hall of fame."""
        self._items = []

    def __len__(self) -> int:
        """Get number of individuals in hall of fame."""
        return len(self._items)

    @overload
    def __getitem__(self, index: int) -> Species: ...

    @overload
    def __getitem__(self, index: slice) -> list[Species]: ...

    def __getitem__(self, index: int | slice) -> Species | list[Species]:
        """Get individual(s) by index.

        Args:
            index: Integer index or slice

        Returns:
            Species instance or list of Species instances
        """
        return self._items[index]

    def __iter__(self) -> Iterator[Species]:
        """Iterate over individuals in hall of fame."""
        return iter(self._items)

    def __repr__(self) -> str:
        """String representation of hall of fame."""
        return f"HallOfFame(maxsize={self.maxsize}, size={len(self)})"


class HallOfFame(NativeHallOfFame):
    """Hall of Fame for Species with convenience methods.

    Extends NativeHallOfFame with additional properties for genetic programming.
    """

    @property
    def best(self) -> Species:
        """Get the best individual in the hall of fame.

        Returns:
            The Species instance with the highest fitness

        Raises:
            IndexError: If hall of fame is empty
        """
        return cast(Species, self[0])
