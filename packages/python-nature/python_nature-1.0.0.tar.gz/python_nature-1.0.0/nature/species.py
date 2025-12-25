"""
Species classes for genetic programming evolution.

This module defines the Species and Population classes that manage individuals
in evolutionary algorithms. Species represents a single evolved program with
its associated tree structure and fitness metrics, while Population manages
collections of Species instances.
"""

import inspect
import math
import sys
from uuid import UUID
from copy import deepcopy
from functools import wraps
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Callable,
    ParamSpec,
    Self,
    Sequence,
    TypeVar,
    cast,
    get_args,
    get_origin,
)
from uuid import uuid4

import numpy as np

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from nature import evaluator
from nature.chromosome import Chromosome
from nature.codons import Codon
from nature.random import Random
from nature.tree import Tree
from nature.typing import SpeciesArray
from nature.utils import is_debug

P = ParamSpec("P")
R = TypeVar("R")


def extract_type_and_symbol(annotation: type) -> tuple[type, str | None]:
    """
    Extract real type and optional symbol name from type annotation.

    Supports Annotated[type, 'symbol_name'] for cleaner symbolic type definitions.
    Falls back to the annotation itself if not Annotated.

    Args:
        annotation: Type annotation (may be Annotated or regular type)

    Returns:
        Tuple of (real_type, symbol_name) where:
        - real_type: The actual Python type (e.g., float, int)
        - symbol_name: String symbol if Annotated, None otherwise

    Examples:
        >>> extract_type_and_symbol(float)
        (float, None)

        >>> extract_type_and_symbol(Annotated[float, 'x'])
        (float, 'x')

        >>> extract_type_and_symbol(Annotated[int, 'count', 'extra_metadata'])
        (int, 'count')  # Uses first metadata item
    """
    origin = get_origin(annotation)

    if origin is Annotated:
        args = get_args(annotation)
        if len(args) >= 2:
            real_type = args[0]
            symbol_candidate = args[1]

            # Only use as symbol if it's a string
            if isinstance(symbol_candidate, str):
                return real_type, symbol_candidate

            # Non-string metadata, treat as regular type
            return real_type, None

    # Not Annotated or malformed - use as-is
    return annotation, None


def evolve(
    capacity: int,
    sigma: int | float | None = None,
    codons: Sequence[Codon | Sequence] = [],
    seed: int | None = None,
    k_sigma: float = 2.0,
    mutation_rate: float = 1.0,
    enabled: bool = True,
):
    """
    Decorator to mark a method for genetic programming evolution.

    Transforms a method into an evolvable genetic program by creating a
    Chromosome that defines how the method's logic will be evolved. The
    decorated method becomes a wrapper that executes the evolved tree.

    Args:
        capacity: Maximum tree size (number of nodes)
        sigma: Standard deviation for tree size variation (default: 0.34 * capacity)
        codons: List of allowed codons (functions/terminals) for building trees
        seed: Random seed for reproducible evolution
        k_sigma: Multiplier for sigma in mutation operations (default: 2.0)
        mutation_rate: Probability of mutation per tree node (default: 1.0)
        enabled: If False, method runs normally without evolution

    Returns:
        Decorated function that executes via evolved tree

    Example:
        >>> class MySpecies(Species):
        >>>     @evolve(capacity=50, codons=[Add(), Sub(), Int(0, 100)])
        >>>     def compute(self, x: int) -> int:
        >>>         '''Placeholder - will be replaced by evolved tree'''
        >>>         return x
        >>>
        >>> # After evolution, compute() executes the evolved tree structure
    """

    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        if not enabled:
            return func

        sig = inspect.signature(func)
        method_name = func.__name__
        # Extract typed parameters for chromosome input specification
        input_dict: dict[str, type | str] = {}

        for k, param in sig.parameters.items():
            # Ignore the arg if not annotated, like *args, **kwargs
            if param.annotation == inspect._empty:
                continue
            if "Union" in type(param.annotation).__name__:
                raise ValueError(
                    f'evolved method "{method_name}" cannot have polymorphic arguments'
                )
            else:
                # Extract real type and symbol from Annotated if present
                real_type, symbol_name = extract_type_and_symbol(param.annotation)

                # Use symbol string if provided, otherwise use real type
                input_dict[k] = symbol_name if symbol_name is not None else real_type

        # Extract return type and symbol
        return_real_type, return_symbol = extract_type_and_symbol(sig.return_annotation)
        output_spec = return_symbol if return_symbol is not None else return_real_type

        chromosome = Chromosome(
            name=method_name,
            mu=capacity,
            sigma=sigma or (capacity * 0.68 / 2),
            k_sigma=k_sigma,
            input=input_dict,
            output=output_spec,
            mutation_rate=mutation_rate,
            codons=codons,
            seed=seed,
            # min_input_depth=min_input_depth,
        )

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            return self.trees[method_name].execute(*args, **kwargs)

        setattr(wrapper, "chromosome", chromosome)
        wrapper.__name__ = method_name
        return wrapper  # type: ignore

    return decorator


class NativeFitness:
    """Native fitness class for multi-objective optimization.

    Replaces DEAP's Fitness class with a native Python implementation.
    Supports both single and multi-objective optimization with weighted objectives.

    API:
        - Use .set_values(values) to set fitness (handles float or sequence)
        - Use del .values to invalidate fitness
        - Read .values, .wvalues, .valid as properties

    Attributes:
        weights: Tuple of floats defining optimization direction for each objective
                 (1.0 = maximize, -1.0 = minimize)
        values: Tuple of raw fitness values for each objective
        wvalues: Computed weighted values (values * weights) - read-only property
        valid: Boolean indicating if fitness has been set - read-only property

    Comparison Logic:
        Uses lexicographic ordering - compares weighted values left-to-right:
        fitness1 > fitness2 if first wvalue is greater, or if equal, second is greater, etc.

    Domination Logic (Pareto):
        fitness1 dominates fitness2 if:
        - All objectives: fitness1.wvalues[i] >= fitness2.wvalues[i]
        - At least one: fitness1.wvalues[i] > fitness2.wvalues[i]

    Example:
        >>> # Single objective (maximize)
        >>> f = NativeFitness()
        >>> f.weights = (1.0,)
        >>> f.values = (10.5,)
        >>> f.wvalues  # (10.5,)
        >>>
        >>> # Multi-objective (maximize first, minimize second)
        >>> f = NativeFitness()
        >>> f.weights = (1.0, -1.0)
        >>> f.values = (10.0, 5.0)
        >>> f.wvalues  # (10.0, -5.0)
    """

    # Epsilon tolerance for floating point comparisons
    _EPSILON = 1e-9

    def __init__(self, values: Sequence[float] | tuple[float, ...] = ()):
        """Initialize fitness with optional values.

        Args:
            values: Initial fitness values (default: empty tuple)
        """
        # Always initialize instance weights (no hasattr checks needed)
        self._weights: tuple[float, ...] = ()

        # Internal storage for values
        self._values: tuple[float, ...] = ()

        # Set values if provided
        if values:
            self._values = tuple(values)

    @property
    def weights(self) -> tuple[float, ...]:
        """Get optimization weights for each objective."""
        return self._weights

    @weights.setter
    def weights(self, weights: Sequence[float] | tuple[float, ...]) -> None:
        """Set optimization weights for each objective."""
        self._weights = tuple(weights)

    @property
    def values(self) -> tuple[float, ...]:
        """Get raw fitness values (read-only).

        To set values, use .set_values() method instead.
        """
        return self._values

    @values.setter
    def values(self, values: Sequence[float] | tuple[float, ...]) -> None:
        """Set raw fitness values.

        Note: Prefer using .set_values() method for setting values.
        This setter is kept for backward compatibility.
        """
        self._values = tuple(values)

    @values.deleter
    def values(self) -> None:
        """Delete fitness values (reset to empty tuple)."""
        self._values = ()

    @property
    def wvalues(self) -> tuple[float, ...]:
        """Get weighted fitness values (values * weights)."""
        if not self._values or not self.weights:
            return ()
        return tuple(v * w for v, w in zip(self._values, self.weights))

    @property
    def valid(self) -> bool:
        """Check if fitness has been set with valid values.

        Returns False if:
        - No values set (empty tuple)
        - Any value is NaN
        - Any value is infinite

        Returns:
            True if fitness is valid, False otherwise
        """
        if len(self._values) == 0:
            return False

        # Check for NaN or Inf values
        for val in self._values:
            if math.isnan(val) or math.isinf(val):
                return False

        return True

    def dominates(self, other: "NativeFitness") -> bool:
        """Check if this fitness dominates another (Pareto domination).

        Self dominates other if:
        - All objectives: self.wvalues[i] >= other.wvalues[i] (with epsilon tolerance)
        - At least one: self.wvalues[i] > other.wvalues[i] (strict inequality)

        Args:
            other: Other fitness to compare against

        Returns:
            True if self dominates other, False otherwise
        """
        if not self.valid or not other.valid:
            return False

        not_equal = False
        for self_wval, other_wval in zip(self.wvalues, other.wvalues):
            if self_wval < other_wval - self._EPSILON:
                # Self is worse in this objective
                return False
            elif self_wval > other_wval + self._EPSILON:
                # Self is better in this objective
                not_equal = True

        # Dominates only if better in at least one objective
        return not_equal

    def __lt__(self, other: "NativeFitness") -> bool:
        """Lexicographic less-than comparison."""
        if not isinstance(other, NativeFitness):
            return NotImplemented
        return self.wvalues < other.wvalues

    def __le__(self, other: "NativeFitness") -> bool:
        """Lexicographic less-than-or-equal comparison."""
        if not isinstance(other, NativeFitness):
            return NotImplemented
        return self.wvalues <= other.wvalues

    def __gt__(self, other: "NativeFitness") -> bool:
        """Lexicographic greater-than comparison."""
        if not isinstance(other, NativeFitness):
            return NotImplemented
        return self.wvalues > other.wvalues

    def __ge__(self, other: "NativeFitness") -> bool:
        """Lexicographic greater-than-or-equal comparison."""
        if not isinstance(other, NativeFitness):
            return NotImplemented
        return self.wvalues >= other.wvalues

    def __eq__(self, other: object) -> bool:
        """Equality comparison based on wvalues."""
        if not isinstance(other, NativeFitness):
            return NotImplemented
        return self.wvalues == other.wvalues

    def __ne__(self, other: object) -> bool:
        """Inequality comparison based on wvalues."""
        if not isinstance(other, NativeFitness):
            return NotImplemented
        return self.wvalues != other.wvalues

    def __hash__(self) -> int:
        """Hash based on wvalues for use in sets/dicts."""
        return hash(self.wvalues)

    def __repr__(self) -> str:
        """String representation showing weights and values."""
        return f"{type(self).__name__}(weights={self.weights}, values={self.values})"

    def __str__(self) -> str:
        """Human-readable string showing wvalues."""
        return f"Fitness({self.wvalues})"

    def __deepcopy__(self, memo):
        """Deep copy preserving weights and values."""
        clone = type(self)()
        clone.weights = tuple(self.weights)
        clone._values = tuple(self.values)  # Direct assignment to avoid setter
        return clone

    def __getstate__(self):
        """Get state for pickling."""
        return {
            "weights": self.weights,
            "values": self.values,
        }

    def __setstate__(self, state):
        """Restore state from pickling."""
        self._weights = state["weights"]
        self._values = state["values"]


class SpeciesFitness(NativeFitness):
    """Fitness class for Species with extended functionality.

    Extends NativeFitness with additional methods for genetic programming:
    - set_values(): Flexible value setting (single float or sequence)
    - score(): Sum of weighted values
    - worst: Worst possible fitness values
    """

    def __init__(
        self,
        weights: Sequence[float] | None = None,
        values: Sequence[float | int] | None = None,
    ):
        """Initialize SpeciesFitness with weights and values.

        Args:
            weights: Optimization weights (1.0 = maximize, -1.0 = minimize)
            values: Initial fitness values
        """
        # Initialize parent class (sets _weights and _values to empty)
        super().__init__()

        # Set weights if provided
        if weights is not None:
            self._weights = tuple(weights)

        # Set values if provided
        if values is not None:
            self.set_values(values)

    def set_values(self, values: Sequence[float] | float) -> None:
        """Set fitness values with flexible input types.

        Args:
            values: Either a single float or sequence of floats
        """
        try:
            if isinstance(values, (int, float)):
                self.values = (float(values),)
            else:
                self.values = tuple(float(x) for x in values)
        except Exception as exc:
            if is_debug():
                breakpoint()
            else:
                raise

    def score(self) -> float:
        """Calculate total fitness score (sum of weighted values).

        Returns:
            Sum of all weighted fitness values
        """
        return float(np.sum(self.wvalues))

    @property
    def worst(self) -> tuple[float, ...]:
        """Get worst possible fitness values for each objective.

        Returns:
            Tuple of negative infinity for maximization objectives,
            positive infinity for minimization objectives
        """
        return tuple([-w * float("inf") for w in self.weights])


def get_size(obj, seen=None):
    """Recursively finds the total size of an object, including nested attributes."""
    if seen is None:
        seen = set()

    obj_id = id(obj)
    if obj_id in seen:
        return 0  # Avoid double-counting

    seen.add(obj_id)
    size = sys.getsizeof(obj)  # Base size of the object

    # Handle different object types
    if isinstance(obj, dict):
        size += sum(get_size(k, seen) + get_size(v, seen) for k, v in obj.items())
    elif isinstance(obj, (list, tuple, set, frozenset)):
        size += sum(get_size(i, seen) for i in obj)
    elif hasattr(obj, "__dict__"):  # For objects with __dict__ (custom objects)
        size += get_size(obj.__dict__, seen)
    elif hasattr(obj, "__slots__"):  # For objects using __slots__
        size += sum(
            get_size(getattr(obj, slot), seen) for slot in obj.__slots__ if hasattr(obj, slot)
        )

    return size


class Species:
    """Base class for genetically evolved species.

    Species are genetically programmable entities that evolve through genetic
    algorithms to optimize fitness objectives. Each species has:
    - Chromosomes: Genetic structure defining evolvable methods
    - Trees: Expression trees built from chromosomes
    - Fitness: Multi-objective fitness values
    - Params: Hyperparameters saved to database

    **IMPORTANT: params vs ctx distinction**

    - **params** (self.params):
        - Hyperparameters that configure the species behavior
        - Serialized to JSONB and saved to database with the species
        - Examples: symbol, version, margin, leverage, seed, training window
        - Must be JSON-serializable (no DataFrames, complex objects, etc.)
        - All dict keys must be strings (JSONB requirement)

    - **ctx** (passed to evaluate() as **kwargs):
        - Runtime context data passed during evolution
        - Ephemeral - NOT saved to database
        - Passed to evaluate() via **kwargs
        - Examples: profiling data, calibration objects, DataFrames, temporary state
        - Can contain non-serializable objects

    Example usage:
        ```python
        # In evolution script:
        ctx = {
            "indicator_profile": profile,  # Runtime data (ephemeral)
            "filter_calibration": calibration,  # Runtime data (ephemeral)
            "objectives": objectives,  # Could be in params, but ctx for flexibility
        }

        params = {
            "symbol": "ETH",  # Hyperparam (saved to DB)
            "version": "test-v1",  # Hyperparam (saved to DB)
            "margin": 250,  # Hyperparam (saved to DB)
        }

        # Evolver passes ctx to evaluate():
        species.evaluate(bars, **ctx)  # ctx NOT saved to database

        # Species.save() serializes params to JSONB:
        species.save(db)  # Only params saved to database
        ```
    """

    chromosomes: dict[str, Chromosome]
    chromosome_name_mutation_sample_pool: Sequence[str] = []
    random = Random()

    Evaluator = evaluator.Evaluator

    def __init_subclass__(cls, **kwargs):
        """
        Initialize Species subclass by collecting chromosomes and building mutation pool.

        This hook runs when a Species subclass is created. It:
        1. Scans the class for @evolve-decorated methods (identified by chromosome attribute)
        2. Collects them into cls.chromosomes dict
        3. Builds weighted mutation sample pool for O(1) random selection

        The mutation pool is weighted by each chromosome's mutation_rate, enabling
        probability-weighted random tree selection during mutation operations.

        Note: Only scans attributes defined in THIS class (cls.__dict__), not inherited
        attributes, to match the original metaclass behavior.
        """
        super().__init_subclass__(**kwargs)

        # Initialize class-level attributes
        cls.chromosomes = chromosomes = cast(dict[str, Chromosome], {})

        min_chromosome_mutation_rate = 1.0

        # Scan only attributes defined in THIS class (not inherited)
        # This matches the metaclass behavior which scanned dct.values()
        for obj in cls.__dict__.values():
            chromosome = cast(Chromosome | None, getattr(obj, "chromosome", None))
            if chromosome:
                chromosomes[chromosome.name] = chromosome
                min_chromosome_mutation_rate = min(
                    chromosome.mutation_rate, min_chromosome_mutation_rate
                )

        # Build sample pool for random probability-weighted tree selection
        # during species mutation:
        chromosome_name_mutation_sample_pool = []
        for c in chromosomes.values():
            chromosome_name_mutation_sample_pool.extend(
                [c.name] * round(10 * max(1, c.mutation_rate / min_chromosome_mutation_rate))
            )

        cls.chromosome_name_mutation_sample_pool = np.array(
            chromosome_name_mutation_sample_pool, dtype=str
        )  # type: ignore

    def __init__(
        self,
        fitness: SpeciesFitness | None = None,
        trees: dict[str, Tree] | None = None,
        params: Any | None = None,
        db_id: Any = None,
        db_table: str | None = None,
    ) -> None:
        self.fitness = fitness or SpeciesFitness()
        self.trees: dict[str, Tree] = trees or {}
        self.params: Any = params or {}
        self.db_id = db_id
        self.db_table = db_table
        self._default_id = uuid4()
        self.valid = True

    @property
    def id(self) -> Any:
        return self.db_id or self._default_id

    def __eq__(self, other: object) -> bool:
        if other is None:
            return False
        return False
        # return all(
        #     own_tree.similarity(other_tree) == 1
        #     for own_tree, other_tree in zip(
        #         self.trees.values(), cast(Species, other).trees.values()
        #     )
        # )

    def __hash__(self) -> int:
        return int(self.db_id.hex, 16) if self.db_id else int(self._default_id.hex, 16)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.id})"

    def save(self, db: "Session | None" = None, tags: Sequence[str] | None = None) -> Any:
        from nature.db.models import SpeciesState
        from nature.db.session import sync_session

        with sync_session(db, autocommit=True) as db:
            return SpeciesState.save(self, session=db, tags=tags)

    @classmethod
    def load(cls, id: Any, db: "Session | None" = None, use_cache=True) -> Self:
        from nature.db.models import SpeciesState

        if isinstance(id, (UUID, str)):
            id = UUID(str(id))
            cached = SpeciesState.cache.get(id) if use_cache else None
            if cached is None:
                return cast(Self, SpeciesState.fetch_by_id(id, session=db, use_cache=use_cache))
            else:
                return cast(Self, cached)
        elif isinstance(id, Species):
            return cast(Self, id)
        else:
            raise ValueError(f"unrecognized species id: {id}")

    @classmethod
    def delete_chromosome(cls, name: str):
        pool = cast(np.ndarray, cls.chromosome_name_mutation_sample_pool)
        cls.chromosome_name_mutation_sample_pool = cast(Sequence, pool[pool != name])
        cls.chromosomes.pop(name, None)

    @classmethod
    def spawn(cls, n: int, params: dict | Any | None = None) -> "Population":
        context = {"params": params}
        return Population(
            species_type=cls,
            instances=[
                cls(
                    fitness=SpeciesFitness(),
                    trees={
                        c.name: Tree(chromosome=c, context=context).build(interpolate=True)
                        for c in cls.chromosomes.values()
                    },
                    params=params,
                )
                for _ in range(n)
            ],
        )

    def compile(self) -> Self:
        for tree in self.trees.values():
            tree.compile()
        return self

    def render_call_graphs(self, distinct_colors_min_depth=2) -> None:
        Tree.render_call_graph(
            self.trees,
            title=f"{type(self).__name__}" + f"_{self.db_id or self.id}",
            distinct_colors_min_depth=distinct_colors_min_depth,
        )

    def copy(self, copy_fitness=False) -> Self:
        return type(self)(
            fitness=SpeciesFitness(
                weights=self.fitness.weights,
                values=cast(Any, tuple(self.fitness.values)) if copy_fitness else None,
            ),
            trees={k: Tree.copy(v) for k, v in self.trees.items()},
            params=deepcopy(self.params),
        )

    def mutate(self) -> bool:
        tree_name = self.random.np_choice(self.chromosome_name_mutation_sample_pool)
        original_tree = self.trees[tree_name]
        tree = Tree.copy(original_tree)
        success = tree.mutate()
        if success and tree.validate_size():
            self.trees[tree_name] = tree
            return True
        return False

    def mate(self, other: Self) -> Self | None:
        tree_name = self.random.np_choice(self.chromosome_name_mutation_sample_pool)
        mother, father = self, other
        mother = mother.copy()
        mother_tree = mother.trees[tree_name]
        father_tree = father.trees[tree_name]
        if mother_tree.graft(father_tree) and mother_tree.validate_size():
            return mother


class Population:
    def __init__(
        self,
        species_type: type[Species],
        instances: Sequence[Species],
        hof_size: int = 30,
    ) -> None:
        from nature.hof import HallOfFame

        self.species_type = species_type
        self.instances: SpeciesArray = np.array(instances, dtype=object)
        self.size = len(instances)
        self.hof = HallOfFame(hof_size)

    def replace(self):
        params = self.instances[0].params
        new_pop = self.species_type.spawn(self.size, params)
        self.instances = new_pop.instances
        self.size = len(self.instances)

    @property
    def best(self) -> Species:
        return self.hof.best
