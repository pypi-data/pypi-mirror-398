"""Nature - A strongly-typed genetic programming framework.

Nature is a hybrid genetic programming and grammar evolution framework that
evolves solutions as instance methods directly on Python classes. It combines
tree-based genetic programming with a grammar-guided codon system for automatic
program discovery through evolutionary search.

Example - Symbolic Regression with Type Wiring:
    >>> from nature import Species, evolve
    >>> from nature.codon import Add, Cast, Float, Int, Mul, PowN
    >>>
    >>> class x_float(float):
    ...     pass
    >>>
    >>> class y_float(float):
    ...     pass
    >>>
    >>> class Regressor(Species):
    ...     @evolve(
    ...         capacity=30,
    ...         codons=[
    ...             [Float(min=-10, max=10, dec=1, out="coeff"), Int(min=0, max=5, out="power")],
    ...             [
    ...                 PowN(in_base=x_float, in_power="power", out="term"),
    ...                 Mul(in_a="coeff", in_b="term", out="factor"),
    ...                 Add(in_a="factor", in_b="factor", out="expr", bias=3),
    ...                 Add(in_a="factor", in_b="expr", out="expr", bias=1),
    ...             ],
    ...             Cast(in_x="expr", out=y_float),
    ...         ],
    ...     )
    ...     def regress(self, x: x_float) -> y_float:
    ...         raise NotImplementedError()
    >>>
    >>> population = Regressor.spawn(n=200)
"""

__version__ = "0.1.0"

import os

from nature.scikit_helpers import set_scikit_n_threads
from nature.logging import logger

# Configure scipy threading if environment variable is set
_n_scipy_threads = os.environ.get("NATURE_SCIKIT_NUM_THREADS")
if _n_scipy_threads:
    n_scipy_threads = int(os.environ.get("NATURE_SCIKIT_NUM_THREADS", "2"))
    logger.info(f"scipy internal process count set to {n_scipy_threads}")
    set_scikit_n_threads(n_scipy_threads)

# Core classes - always import these
from nature.species import Species, evolve, Population
from nature.chromosome import Chromosome
from nature.tree import Tree
from nature.codon import Codon
from nature.evaluator import Evaluator
from nature.hof import HallOfFame
from nature.selection import TournamentSelection, SelectionAlgorithm
from nature.incubators.incubator import Incubator

# Re-export the codon module for convenience
from nature import codon

__all__ = [
    # Version
    "__version__",
    # Core classes
    "Species",
    "evolve",
    "Population",
    "Chromosome",
    "Tree",
    "Codon",
    # Evolution
    "Evaluator",
    "Incubator",
    "HallOfFame",
    # Selection
    "TournamentSelection",
    "SelectionAlgorithm",
    # Modules
    "codon",
    # Utilities
    "logger",
]
