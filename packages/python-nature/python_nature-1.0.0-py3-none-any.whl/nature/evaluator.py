from typing import Annotated, Any, Sequence, cast
from uuid import uuid4

from numpy import ndarray

from nature.utils import flatten

SpeciesType = Annotated[Any, "SpeciesType"]


class Evaluator:
    def __init__(
        self,
        weights: float | Sequence[float] | None = None,
        ctx: dict | None = None,
        parsimony_coefficient: float = 0.0,
    ) -> None:
        self.id = uuid4().hex
        self._is_ready = False
        self._fixed_weights = flatten(weights) if weights else None
        self.ctx: dict = ctx or {}
        self.parsimony_coefficient = parsimony_coefficient

    @property
    def weights(self) -> Sequence[float]:
        return self._fixed_weights or self.default_weights

    @property
    def default_weights(self) -> Sequence[float]:
        return (1,)

    @property
    def is_ready(self):
        return self._is_ready

    def set_weights(self, weights: Sequence[float]):
        self._fixed_weights = tuple(weights)

    def setup(self):
        self.on_setup()
        self._is_ready = True

    def evaluate(self, species: SpeciesType, i_gen: int) -> float | Sequence[float]:
        raw_fitness = self.on_evaluate(species, i_gen)

        # Apply parsimony pressure (penalize tree bloat)
        if self.parsimony_coefficient > 0:
            total_nodes = sum(tree.size for tree in species.trees.values())
            penalty = self.parsimony_coefficient * total_nodes

            # Apply penalty to fitness (works for both minimization and maximization)
            if isinstance(raw_fitness, tuple):
                return tuple(f - penalty for f in raw_fitness)
            else:
                return cast(float, raw_fitness) - penalty

        return raw_fitness

    def on_setup(self):
        pass

    def on_batch_received(self, batch: ndarray, i_gen: int):
        pass

    def on_batch_evaluated(self, batch: ndarray, i_gen: int):
        pass

    def on_evaluate(self, species: SpeciesType, i_gen: int) -> float | Sequence[float]:
        return species.fitness.worst
