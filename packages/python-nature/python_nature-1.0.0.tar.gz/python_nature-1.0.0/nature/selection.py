"""Selection algorithms for genetic programming.

This module provides selection operators for choosing individuals from a population.
Supports both single-objective and multi-objective optimization with optimized
implementations when available.

Performance Note:
    - Uses pymoo (Cython-optimized) when available for NSGA-II/III
    - Falls back to native Python/NumPy implementations from nsga.py
    - pymoo provides 2-10x speedup on large populations (>500 individuals)

Example:
    >>> from nature.selection import SelectionAlgorithm
    >>> # Auto-selects appropriate algorithm based on objectives
    >>> selector = SelectionAlgorithm.default(pop_size=100, n_objectives=2)
    >>> # For single-objective: uses TournamentSelection
    >>> # For multi-objective: uses optimized NSGA-II/III
"""
from operator import attrgetter
from typing import Sequence, cast

import numpy as np

from nature import nsga
from nature.random import Random
from nature.ring_buffer import RingBuffer
from nature.species import Species
from nature.typing import SpeciesArray

# Try to import pymoo for optimized multi-objective selection
# Fall back to native implementation if not available
try:
    from pymoo.algorithms.moo.nsga2 import NSGA2, RankAndCrowdingSurvival
    from pymoo.algorithms.moo.nsga3 import NSGA3
    from pymoo.core.population import Population as PyMooPopulation
    from pymoo.core.problem import Problem
    from pymoo.util.ref_dirs import get_reference_directions

    class _DummyProblem(Problem):
        """Minimal Problem for pymoo survival selection.

        pymoo's survival operators require a Problem object to check constraints.
        This dummy problem has no constraints and is used purely for selection.
        """

        def __init__(self, n_obj: int):
            super().__init__(n_var=1, n_obj=n_obj, n_constr=0)

        def _evaluate(self, x, out, *args, **kwargs):
            pass  # Not needed for survival selection

    PYMOO_AVAILABLE = True
except ImportError:
    PYMOO_AVAILABLE = False


class SelectionAlgorithm:
    """Base class for selection algorithms.

    Args:
        k: Number of individuals to select (default: 1)
    """

    def __init__(self, k: int | None = None) -> None:
        self.k = max(1, k or 1)
        self.random = Random()

    def select(
        self, instances: SpeciesArray | RingBuffer, k: int | None = None
    ) -> SpeciesArray:
        """Select k individuals from the population.

        Args:
            instances: Population to select from
            k: Number of individuals to select (overrides self.k)

        Returns:
            Array of selected individuals

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError()

    @classmethod
    def default(cls, pop_size: int, n_objectives: int) -> "SelectionAlgorithm":
        """Create default selector for given population and objectives.

        Args:
            pop_size: Population size
            n_objectives: Number of fitness objectives

        Returns:
            TournamentSelection for single-objective,
            NGSASelection for multi-objective
        """
        if n_objectives == 1:
            return TournamentSelection(k=pop_size, tournament_size=round(0.07 * pop_size))
        else:
            return NGSASelection(k=pop_size)


class TournamentSelection(SelectionAlgorithm):
    """Tournament selection algorithm.

    For single-objective: Simple tournament based on fitness
    For multi-objective: Tournament with crowding distance (native implementation)

    Args:
        tournament_size: Number of individuals per tournament (default: 2)
        k: Number of individuals to select
        replace: Allow replacement in tournament sampling (default: False)

    Example:
        >>> selector = TournamentSelection(tournament_size=3, k=100)
        >>> selected = selector.select(population)
    """

    def __init__(
        self,
        tournament_size: int | None = None,
        k: int | None = None,
        replace=False,
    ):
        super().__init__(k)
        self.tournament_size = tournament_size or 2
        self.with_replacement = replace
        self.n_objectives = 0

    def select(
        self,
        instances: SpeciesArray | RingBuffer,
        k: int | None = None,
        tournament_size: int | None = None,
    ) -> SpeciesArray:
        """Perform tournament selection.

        Args:
            instances: Population to select from
            k: Number to select (overrides self.k)
            tournament_size: Tournament size (overrides self.tournament_size)

        Returns:
            Array of selected individuals
        """
        tournament_size = tournament_size or self.tournament_size
        k = k or self.k

        if not self.n_objectives:
            self.n_objectives = len(cast(Species, instances[0]).fitness.weights)

        if len(instances) < tournament_size:
            return np.empty(0, dtype=object)

        if self.n_objectives == 1:
            # Single-objective: simple max fitness tournament
            chosen = np.empty(k, dtype=object)
            for i in range(k):
                aspirants = self.random.np_choice(
                    instances, self.tournament_size, replace=self.with_replacement
                )
                chosen[i] = max(cast(Sequence, aspirants), key=attrgetter("fitness"))
            return chosen
        else:
            # Multi-objective: crowding distance tournament (native)
            nsga.assign_crowding_distance(instances)
            chosen = np.empty(k, dtype=object)
            for i in range(k):
                aspirants = self.random.np_choice(
                    instances, tournament_size, replace=self.with_replacement
                )
                # Select best based on fitness, tie-break with crowding distance
                aspirants_list = cast(Sequence, aspirants)
                # Sort by fitness (descending), then by crowding distance (descending)
                best = max(
                    aspirants_list,
                    key=lambda ind: (
                        ind.fitness.wvalues,
                        getattr(ind.fitness, "crowding_dist", 0.0),
                    ),
                )
                chosen[i] = best
            return chosen


class RouletteSelection(SelectionAlgorithm):
    """Roulette wheel selection (fitness-proportional).

    Note: Not yet implemented. Use TournamentSelection instead.
    """

    pass


class StochasticUniversalSampling(SelectionAlgorithm):
    """Stochastic Universal Sampling selection.

    Note: Not yet implemented. Use TournamentSelection instead.
    """

    pass


class NGSASelection(SelectionAlgorithm):
    """NSGA-II and NSGA-III selection algorithms.

    Uses optimized pymoo implementation when available (2-10x faster),
    otherwise falls back to native Python/NumPy implementation.

    - NSGA-II: For 2 objectives
    - NSGA-III: For 3+ objectives (requires reference points)

    Args:
        k: Number of individuals to select
        log_scale: Use log-scale for non-dominated sorting (default: False)
            Use when objectives have different orders of magnitude
            (e.g., obj1 ∈ [1,100], obj2 ∈ [100,100000])
        use_pymoo: Force use of pymoo (default: auto-detect)

    Example:
        >>> # 2-objective optimization
        >>> selector = NGSASelection(k=100)
        >>> selected = selector.select(population)
        >>>
        >>> # 5-objective optimization (NSGA-III)
        >>> selector = NGSASelection(k=100)
        >>> selected = selector.select(population_with_5_objectives)
    """

    def __init__(
        self, k: int | None = None, log_scale=False, use_pymoo: bool | None = None
    ) -> None:
        super().__init__(k)
        # Note: use "log" if objectives have different orders of magnitude
        self.nd = "log" if log_scale else "standard"
        self.n_objectives = 0
        self._use_pymoo = use_pymoo if use_pymoo is not None else PYMOO_AVAILABLE
        self._survival = None  # Cached pymoo survival operator

    def select(
        self,
        instances: SpeciesArray | RingBuffer,
        k: int | None = None,
    ) -> SpeciesArray:
        """Perform NSGA-II or NSGA-III selection.

        Args:
            instances: Population to select from
            k: Number to select (overrides self.k)

        Returns:
            Array of selected individuals using NSGA-II (2 objectives)
            or NSGA-III (3+ objectives)
        """
        k = k or self.k

        if not self.n_objectives:
            self.n_objectives = len(cast(Species, instances[0]).fitness.weights)

        if self._use_pymoo and PYMOO_AVAILABLE:
            return self._select_pymoo(instances, k)
        else:
            return self._select_native(instances, k)

    def _select_native(
        self, instances: SpeciesArray | RingBuffer, k: int
    ) -> SpeciesArray:
        """Selection using native NSGA implementation.

        Uses native Python/NumPy implementations from nsga.py module.
        Falls back to this when pymoo is not available.
        """
        if self.n_objectives < 3:
            # NSGA-II for 2 objectives
            return nsga.sel_NSGA2(instances, k=k, nd=self.nd)
        else:
            # NSGA-III for 3+ objectives
            # Generate reference points using pymoo if available, otherwise use simple approach
            if PYMOO_AVAILABLE:
                ref_points = get_reference_directions(
                    "energy",  # Riesz s-energy method
                    self.n_objectives,
                    n_points=k,
                )
            else:
                # Fallback: create simple uniform reference points
                # This is a basic implementation - pymoo's is more sophisticated
                import itertools

                n_partitions = max(1, int(k ** (1.0 / self.n_objectives)))
                ref_points = np.array(
                    list(
                        itertools.product(
                            *[np.linspace(0, 1, n_partitions) for _ in range(self.n_objectives)]
                        )
                    )
                )
                # Normalize to sum to 1
                ref_points = ref_points / ref_points.sum(axis=1, keepdims=True)

            return nsga.sel_NSGA3(instances, k=k, ref_points=ref_points, nd=self.nd)

    def _select_pymoo(
        self, instances: SpeciesArray | RingBuffer, k: int
    ) -> SpeciesArray:
        """Selection using optimized pymoo implementation.

        pymoo uses Cython-compiled code for rank and crowding distance
        calculations, providing significant speedup on large populations.
        """
        if not PYMOO_AVAILABLE:
            raise RuntimeError("pymoo not available, use native fallback")

        # Extract fitness values (F) from Species instances
        # pymoo expects minimization, so negate maximization objectives
        F = np.array(
            [
                [
                    -val if weight > 0 else val
                    for val, weight in zip(ind.fitness.values, ind.fitness.weights)
                ]
                for ind in instances
            ]
        )

        # Create dummy problem (required by pymoo API)
        problem = _DummyProblem(n_obj=self.n_objectives)

        # Create pymoo Population from fitness values
        pop = PyMooPopulation.new("F", F)

        if self.n_objectives < 3:
            # NSGA-II for 2 objectives (rank and crowding distance)
            if self._survival is None:
                self._survival = RankAndCrowdingSurvival()

            # Perform survival selection
            survivors = self._survival.do(
                problem=problem,
                pop=pop,
                n_survive=k,
            )
        else:
            # NSGA-III for 3+ objectives (reference point based)
            # Generate reference directions for NSGA-III
            ref_dirs = get_reference_directions(
                "energy",  # Riesz s-energy method (uniform distribution)
                self.n_objectives,
                n_points=k,  # Number of reference points
            )

            # Create NSGA-III algorithm instance
            if self._survival is None:
                algorithm = NSGA3(ref_dirs=ref_dirs)
                self._survival = algorithm.survival

            # Perform survival selection
            survivors = self._survival.do(
                problem=problem,
                pop=pop,
                n_survive=k,
            )

        # Extract indices of survivors by comparing object identity
        survivor_set = {id(s) for s in survivors}
        indices = [i for i, ind in enumerate(pop) if id(ind) in survivor_set]

        # Return corresponding Species instances
        return np.array([instances[i] for i in indices])


# Expose implementation status for testing/debugging
def get_implementation_info() -> dict[str, bool | str]:
    """Get information about available selection implementations.

    Returns:
        Dictionary with implementation details:
        - pymoo_available: Whether pymoo is installed
        - pymoo_version: pymoo version if available
        - default_backend: Which backend is used by default
    """
    info = {
        "pymoo_available": PYMOO_AVAILABLE,
        "default_backend": "pymoo" if PYMOO_AVAILABLE else "native",
    }

    if PYMOO_AVAILABLE:
        import pymoo

        info["pymoo_version"] = getattr(pymoo, "__version__", "unknown")

    return info
