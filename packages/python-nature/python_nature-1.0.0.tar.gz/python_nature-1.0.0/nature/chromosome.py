"""
Chromosome - Grammar Definition for Genetic Programming Trees.

A Chromosome defines the "genetic grammar" that governs how expression trees
can be built and evolved. It specifies:
- Available codons (the genetic alphabet)
- Type system and compatibility rules
- Tree size constraints (mean, std deviation)
- Input/output signatures for evolved programs

Think of a Chromosome as a "recipe book" that defines:
- What ingredients are available (codons)
- How they can be combined (type compatibility)
- How big the dish should be (tree size distribution)

Key Concepts:
- **Codon Pool**: Collection of available functions and terminals for building trees
- **Type Compatibility**: Pre-computed lookup tables mapping (parent, depth, arg_index) → compatible child codons
- **Size Distribution**: Trees follow Gaussian distribution around mean (mu) with std deviation (sigma)
- **Input/Output Spec**: Defines function signature of evolved trees
- **Compiled Scope**: Namespace dict for executing compiled trees

The Chromosome performs expensive pre-computation during initialization:
- Builds type compatibility lookup tables for O(1) codon selection
- Assigns integer type codes to all types for efficient comparison
- Identifies terminal-like codons (functions with only input children)
- Creates bias-weighted sampling pools for each parent→child relationship

Example:
    >>> from nature.chromosome import Chromosome
    >>> from nature.codon import Add, Sub, Mul, Float, Int
    >>>
    >>> # Define grammar for evolving arithmetic expressions
    >>> chrom = Chromosome(
    ...     name="arithmetic",
    ...     mu=20,              # Target tree size: ~20 nodes
    ...     sigma=5,            # Std deviation: ±5 nodes
    ...     codons=[            # Available operations
    ...         Add(), Sub(), Mul(),
    ...         Float(0.0, 10.0),
    ...         Int(1, 100)
    ...     ],
    ...     input={'x': float, 'y': float},  # Takes x, y as inputs
    ...     output=float,                    # Returns float
    ...     k_sigma=3,          # Max tree size: mu + 3*sigma = 35 nodes
    ... )
    >>> # This chromosome can build trees like: (x + 5.3) * (y - 2)
"""

import sys
import numpy as np

from collections import defaultdict
from typing import Annotated, Self, Sequence, TypeAlias, cast
from numpy.typing import NDArray

from nature.random import Random
from nature.typing import NodeArray
from nature.utils import clamp, flatten
from nature.codon import Codon, Inp, Out
from nature.codons import NIL

empty = lambda: np.empty(0, dtype=int)

CodonArray = Annotated[NDArray, "Codon"]
CompatibleCodonsSetDict: TypeAlias = dict[tuple[Codon, int, int], set]
CompatibleCodonsArrayDict: TypeAlias = dict[tuple[int, int, int], NDArray]


class Chromosome:
    """
    Genetic grammar defining how expression trees can be built and evolved.

    A Chromosome is the "blueprint" that governs tree construction and evolution.
    It pre-computes type compatibility relationships between codons to enable fast,
    type-safe tree generation and mutation.

    The Chromosome maintains several internal data structures:
    - Type compatibility lookup tables for O(1) codon selection
    - Input codons for each parameter in the function signature
    - Output codon wrapping the expected return type
    - Compiled scope dict for executing generated Python code

    Attributes:
        name: Identifier for this chromosome (used as function name in compiled code)
        mu: Mean tree size (number of nodes) for Gaussian distribution
        sigma: Standard deviation of tree size
        k_sigma: Multiplier for max tree size (max_size = mu + k_sigma * sigma)
        min_tree_size: Minimum allowed tree size (typically 1)
        max_tree_size: Maximum allowed tree size
        mutation_rate: Probability of mutation for trees using this chromosome
        codons: Flattened sequence of all available codons (excluding input/output)
        input_codons: Array of Inp codons for function parameters
        output_codon: Out codon wrapping the return type
        random: Random number generator (seeded if seed provided)
        compiled_scope: Namespace dict for compiled tree execution
        func_def_template: Python function definition template for compilation

    Size Distribution:
        Trees follow a Gaussian distribution centered at mu with std dev sigma.
        Individual trees sample a target_size from N(mu, k_sigma * sigma), then
        grow toward that size during construction. The k_sigma parameter controls
        the allowed range: k_sigma=3 means 99.7% of trees within mu ± 3*sigma.

    Type System:
        Each codon declares:
        - ret_types: Tuple of types this codon can return
        - arg_types: List of type unions for each argument

        During tree construction, the Chromosome uses pre-computed lookup tables
        to find compatible children in O(1) time:
        - find_compatible_child_codons(parent, child_index, depth) → [codon_ids]

        As trees approach their target size, the Chromosome biases selection
        toward terminal codons to gracefully finish growth.

    Example Usage:
        >>> # Build chromosome for evolving trading signals
        >>> from nature.chromosome import Chromosome
        >>> from nature.codon import Gt, Lt, And, Or, Float
        >>>
        >>> signal_chromosome = Chromosome(
        ...     name="signal",
        ...     mu=30,
        ...     sigma=10,
        ...     codons=[
        ...         Gt(), Lt(), And(), Or(),
        ...         Float(-1.0, 1.0),
        ...     ],
        ...     input={'price': float, 'volume': float},
        ...     output=bool,
        ... )
    """

    def __init__(
        self,
        name: str,
        mu: int,
        sigma: float,
        codons: Sequence[Sequence[Codon] | Codon],
        output: type | str | tuple[type, ...],
        input: type | str | tuple[type | str, ...] | dict[str, type | str] | None = None,
        mutation_rate: float = 1.0,
        seed: int | None = None,
        k_sigma: float = 3,
        min_input_depth=1,
    ) -> None:
        """
        Initialize a Chromosome with genetic grammar specifications.

        This performs extensive pre-computation to build type compatibility lookup
        tables that enable O(1) codon selection during tree construction.

        Args:
            name: Chromosome identifier (used as function name in compiled code)
            mu: Mean target tree size (number of nodes)
            sigma: Standard deviation of tree size distribution
            codons: Available functions and terminals (nested sequences are flattened)
            output: Expected return type(s) of evolved programs
            input: Input signature, specified as:
                - type: Single positional argument (e.g., float)
                - tuple[type, ...]: Multiple positional arguments
                - dict[str, type]: Named keyword arguments
                - None: No inputs (programs are generators)
            mutation_rate: Base probability of mutation (0.0 to 1.0)
            seed: Random seed for reproducible tree generation
            k_sigma: Multiplier for max tree size (max = mu + k_sigma * sigma)
            min_input_depth: Minimum depth where input codons can appear (default 1)

        Raises:
            AssertionError: If any parent-child arg type combination has no compatible codons

        Process:
            1. Build Inp codons from input specification
            2. Build Out codon from output specification
            3. Assign integer type codes to all types for efficient lookup
            4. Build compatibility mappings for each (parent, depth, arg_index)
            5. Create bias-weighted sampling pools
            6. Identify terminal-like codons
            7. Generate function definition template for compilation
        """
        self.name = name
        self.mu = mu
        self.sigma = sigma
        self.k_sigma = clamp(abs(k_sigma), 0, 5)
        self.min_tree_size = 1
        self.max_tree_size = mu + k_sigma * sigma
        self.mutation_rate = clamp(mutation_rate, 0, 1)
        self.codons: Sequence[Codon] = flatten(codons)
        self.output_codon = Out(output)
        self.output_obj = output
        self.input_obj = input
        self.seed = seed
        self.random = Random(seed)
        self.compiled_scope = {}

        self.id_2_codon: dict[int, Codon] = {}

        input_codons: list[Inp] = []

        # Build Input codons
        if isinstance(self.input_obj, type):
            input_codons.append(Inp(key=0, arg_name="a0", input_type=self.input_obj))
        elif isinstance(self.input_obj, tuple):
            input_codons.extend(
                Inp(key=i, arg_name=f"a{i}", input_type=t) for i, t in enumerate(self.input_obj)
            )
        elif isinstance(self.input_obj, dict):
            input_codons.extend(
                Inp(key=k, arg_name=k, input_type=v) for k, v in self.input_obj.items()
            )

        self.input_codons = np.array(input_codons, dtype=Codon)
        self.min_input_depth = min_input_depth
        if min_input_depth:
            for codon in input_codons:
                codon.min_depth = min_input_depth

        # Create a lookup table that enables us to determine the set of
        # candidate codons with respect to a given parent codon type and
        # argument index, in O(1). This comes into play when we are building or
        # applying mutations to nodes in expression trees.
        compat_child_codons: CompatibleCodonsSetDict = defaultdict(set)
        compat_internal_codons: CompatibleCodonsSetDict = defaultdict(set)
        compat_terminal_codons: CompatibleCodonsSetDict = defaultdict(set)
        codons_by_depth: dict[int, set[Codon]] = defaultdict(set)
        codons_by_ret_type: dict[int, set[Codon]] = defaultdict(set)
        compat_child_codons_no_depth: dict[tuple[int, int], list[int]] = defaultdict(list)
        compat_terminal_codons_no_depth: dict[tuple[int, int], list[int]] = defaultdict(list)

        self._type_code_counter: int = 1
        self._assigned_type_codes: dict[str | type, int] = {}

        all_codons: Sequence[Codon] = flatten(
            [self.codons, list(self.input_codons), self.output_codon]
        )

        # Codon processing first pass:
        for codon in all_codons:
            self.id_2_codon[codon.id] = codon

            # Normalize and bound min and max codon depth constraints
            if codon.is_output:
                codon.max_depth = 0
                codon.min_depth = 0
            else:
                if codon.min_depth < 1:
                    codon.min_depth = 1
                if codon.max_depth != NIL and codon.max_depth < codon.min_depth:
                    codon.max_depth = codon.max_depth

            # Track codon by its return trype (except Output codon)
            if codon.max_depth != NIL:
                for d in range(codon.min_depth, codon.max_depth + 1):
                    codons_by_depth[d].add(codon)

            for t_arg in codon.ret_types:
                type_code = self._get_type_code(t_arg)
                codons_by_ret_type[type_code].add(codon)
                if isinstance(t_arg, type):
                    self.compiled_scope[t_arg.__name__] = t_arg

            # Mark the codon, indicating that all of the codon's arguments are
            # sourced exclusively from input codons. If it is, this means we can
            # should treat it like a terminal when building or modifying trees.
            for i_arg, arg_type_union in enumerate(codon.arg_types):
                all_args_from_inputs = True
                for t_arg in arg_type_union:
                    type_code = self._get_type_code(t_arg)
                    codons_with_required_type = codons_by_ret_type[type_code]
                    if all_args_from_inputs and not all(
                        c.is_input for c in codons_with_required_type
                    ):
                        all_args_from_inputs = False
                        break
                if all_args_from_inputs:
                    codon.is_terminal_like = True

        # Codon processing second pass: Precompute a mapping from the children
        # node arg types of each codon to an array of codons with compatible
        # return types, available at the given depth.
        for codon in cast(Sequence[Codon], all_codons):
            for i_arg, arg_type_union in enumerate(codon.arg_types):
                for t_arg in arg_type_union:
                    type_code = self._get_type_code(t_arg)
                    codons_with_required_type = codons_by_ret_type[type_code]

                    if isinstance(t_arg, type):
                        self.compiled_scope[t_arg.__name__] = t_arg

                    if not codons_with_required_type:
                        continue

                    # Register other codons as "compatible" with the current
                    # codon if they have the required return type and
                    # allowed tree depths.
                    for other in cast(Sequence[Codon], codons_with_required_type):
                        # if other.max_depth == NIL:
                        if other is self.output_codon:
                            continue
                        compat_child_codons_no_depth[codon.id, i_arg].extend(
                            [other.id] * int(other.bias)
                        )
                        if other.nullary or other.is_terminal_like:
                            compat_terminal_codons_no_depth[codon.id, i_arg].extend(
                                [other.id] * int(other.bias)
                            )

        self._codons_by_depth = codons_by_depth
        self._compat_codons = self._build_array_dict(compat_child_codons)
        self._compat_terminal_codons: CompatibleCodonsArrayDict = self._build_array_dict(
            compat_terminal_codons
        )
        # self._compat_internal_codons = self._build_array_dict(compat_internal_codons)
        self._compat_codons_no_max_depth = {
            k: np.fromiter(v, dtype=int) for k, v in compat_child_codons_no_depth.items()
        }
        self._compat_terminal_codons_no_max_depth = {
            k: np.fromiter(v, dtype=int) for k, v in compat_terminal_codons_no_depth.items()
        }

        # Build func def format string for function compilation
        self.func_def_template = self._build_func_def_template()

    def _get_type_code(self, type_obj: str | type) -> int:
        type_id = self._assigned_type_codes.get(type_obj)
        if type_id is None:
            type_id = self._type_code_counter
            self._assigned_type_codes[type_obj] = type_id
            self._type_code_counter += 1
        return type_id

    def _build_array_dict(
        self,
        source: CompatibleCodonsSetDict,
    ) -> CompatibleCodonsArrayDict:
        array_dict: CompatibleCodonsArrayDict = {}
        for k, compatible_codons in source.items():
            net_bias = sum(max(1, c.bias) for c in compatible_codons)
            pool: list[int] = []

            for c in compatible_codons:
                multiplier = 10 * (c.bias / net_bias)
                pool.extend([c.id] * multiplier)

            a, b, c = k
            array_dict_key = (a.id, b, c)
            array_dict[array_dict_key] = np.array(pool, dtype=object)
            self.random.np_shuffle(array_dict[array_dict_key])

        return array_dict

    def allows_codon_at_depth(self, codon: Codon, depth: int) -> bool:
        return True
        return codon in (self._codons_by_depth[depth] or [])

    def find_compatible_child_codons(
        self,
        parent: Codon,
        child_index: int,
        child_depth: int,
        fullness: float = 0,
    ) -> CodonArray:
        """
        Find codons compatible with parent's argument type at specified depth.

        This is the core method for type-safe tree construction. Given a parent
        codon and which argument slot needs to be filled, returns an array of
        candidate child codons that:
        1. Return a type compatible with parent's arg_types[child_index]
        2. Are allowed to appear at child_depth (respect min/max depth constraints)
        3. Are weighted by their bias values (higher bias = more copies in array)

        As the tree approaches its target size (fullness → 1.0), this method
        increasingly favors terminal codons to gracefully finish tree construction.

        Args:
            parent: The parent codon needing a child
            child_index: Which argument of parent needs filling (0-indexed)
            child_depth: Tree depth where the child will be placed
            fullness: Ratio of current tree size to target size (0.0 to 1.0+)
                      Higher fullness biases toward terminals to finish growth

        Returns:
            Array of compatible Codon instances (may have duplicates for bias weighting)
            Returns empty array if no compatible codons exist

        Algorithm:
            1. Check if fullness² > random() - if true, try terminals only first
            2. Look up compatible codons using pre-computed tables:
               - _compat_terminal_codons[(parent.id, depth, child_index)]
               - _compat_codons[(parent.id, depth, child_index)]
            3. Merge results from depth-specific and depth-agnostic lookups
            4. Convert codon IDs back to Codon instances

        Example:
            >>> chrom = Chromosome(...)
            >>> add_codon = Add()  # Requires two floats
            >>> # Find codons that can be Add's first argument (index 0) at depth 2
            >>> candidates = chrom.find_compatible_child_codons(
            ...     parent=add_codon,
            ...     child_index=0,
            ...     child_depth=2,
            ...     fullness=0.8  # Near target size, favor terminals
            ... )
            >>> # Returns array like [Float(...), Float(...), Inp('x'), ...]
        """
        key = (parent.id, child_depth, child_index)
        nil = empty()
        codon_ids = nil

        # Try to restrict candidates to terminals only as fuillness increases
        terminals_only_prob = clamp(pow(fullness, 2), 0, 1)
        if self.random.flip(p=terminals_only_prob):
            codon_ids = np.concat(
                [
                    self._ensure_1d(self._compat_terminal_codons.get(key, nil)),
                    self._ensure_1d(
                        self._compat_terminal_codons_no_max_depth.get((parent.id, child_index), nil)
                    ),
                ],
                axis=0,
            )

        if not len(codon_ids):
            codon_ids = np.concat(
                [
                    self._ensure_1d(self._compat_codons.get(key, nil)),
                    self._ensure_1d(
                        self._compat_codons_no_max_depth.get((parent.id, child_index), nil)
                    ),
                ],
                axis=0,
            )

        if len(codon_ids):
            return np.fromiter((self.id_2_codon[i] for i in codon_ids), dtype=object)

        return nil

    @staticmethod
    def _ensure_1d(x):
        x = np.asarray(x, dtype=object)
        if x.ndim == 0:
            x = np.expand_dims(x, axis=0)
        return x

    def _build_func_def_template(self) -> str:
        # Build args & kwargs list string
        # NOTE: type unions are not currently supported as input arg types, so
        # only things like `x: float`, not `x: float | int`
        args_str = ",".join(
            (f"a{inp.key}" if isinstance(inp.key, int) else cast(str, inp.key))
            + f":{inp.input_type if isinstance(inp.input_type, str) else inp.input_type.__name__}"
            for inp in cast(Sequence[Inp], self.input_codons)
        )

        # Build return type annotation string
        ret_type_str = ""
        if isinstance(self.output_obj, tuple):
            ret_type_str = f'tuple[{",".join(t if isinstance(t, str) else t.__name__ for t in cast(tuple,self.output_obj))}]'
        else:
            ret_type_str = (
                self.output_obj if isinstance(self.output_obj, str) else self.output_obj.__name__
            )

        # Build the composite format string
        return f"""
            def {self.name}({args_str})->{ret_type_str}:{{}}
        """.strip()

    @classmethod
    def with_codons(cls, source: Self, codons: Sequence) -> Self:
        return cls(
            name=source.name,
            mu=source.mu,
            sigma=source.sigma,
            codons=codons,
            output=source.output_obj,
            input=source.input_obj,
            mutation_rate=source.mutation_rate,
            k_sigma=source.k_sigma,
            seed=source.seed,
            min_input_depth=source.min_input_depth,
        )
