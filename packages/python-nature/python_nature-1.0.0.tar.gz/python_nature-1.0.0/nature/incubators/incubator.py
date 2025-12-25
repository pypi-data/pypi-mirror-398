"""
Incubator - Evolution Orchestration and Coordination.

The Incubator manages the complete evolutionary process for a population:
- Parallel fitness evaluation using multiprocessing
- Genetic operators (selection, mutation, crossover)
- Elite migration between multiple incubator peers
- Hall of Fame tracking for best solutions
- Generation-by-generation coordination

Key concepts:
- Incubator: Central coordinator running evolution algorithm
- TransferSender/Receiver: Background threads for elite exchange
- Batch evaluation: Parallel fitness computation across worker processes
- Elite injection: Periodically inject hall-of-fame elites into population

Typical workflow:
1. Create Incubator with initial Population
2. Run evolve() for N generations
3. Each generation:
   - Evaluate fitness in parallel (batch_evaluate)
   - Select parents (tournament/roulette)
   - Create offspring (mutate_or_mate)
   - Replace population
   - Update hall of fame
"""
from __future__ import annotations

import multiprocessing
import os
import pickle
from threading import Thread
import traceback
import signal


from multiprocessing import Pool, Queue, Value
from multiprocessing.sharedctypes import Synchronized
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from math import ceil
from time import sleep
from typing import Any, Callable, Self, Sequence, cast

import numpy as np
from nature.chromosome import Chromosome
from nature.codons import Codon
from nature.evaluator import Evaluator
from nature.hof import HallOfFame
from nature.incubators.population_sizing import PopulationSizeStrategy
from nature.random import Random
from nature.selection import SelectionAlgorithm
from nature.species import Population, Species
from nature.typing import SpeciesArray
from nature.utils import builtin_id, clamp, flatten, is_debug, iter_batches
from nature.logging import logger

IncubatorCallback = Callable[[int, "Incubator", dict], None]


class TransferSender(Thread):
    """
    Background thread that sends elite individuals to peer incubators.

    Runs continuously, processing requests from the queue to transfer
    selected individuals (with hall-of-fame elites injected) to other
    incubators in a distributed evolution setup.
    """
    def __init__(self, incubator: "Incubator") -> None:
        super().__init__(daemon=True)
        self._incubator = incubator
        self.in_queue = Queue()  # (recipient_id, count) tuples

    def run(self) -> None:
        """Process transfer requests until None is received (shutdown signal)."""
        while True:
            task = cast(tuple[int, int] | None, self.in_queue.get())
            if task is None:
                break

            recipient_id, count = task

            # Select random individuals from population
            selected = cast(
                SpeciesArray,
                self._incubator.random.np_choice(
                    self._incubator.population.instances, count, replace=False
                ),
            )

            # Inject elites from hall of fame before sending
            self._incubator.inject_elites_from_hof(
                selected,
                self._incubator.population.hof,
                rounds=int(0.1 * self._incubator.population.size),
            )

            # Send to peer's receiver queue
            peer = self._incubator.peers[recipient_id]
            out_queue = peer._transfer_receiver.in_queue
            out_queue.put(selected)


class TransferReceiver(Thread):
    """
    Background thread that receives elite individuals from peer incubators.

    Accumulates received individuals in arrays_received list for the
    Incubator to integrate into its population at opportune times.
    """
    def __init__(self, incubator: "Incubator") -> None:
        super().__init__(daemon=True)
        self._incubator = incubator
        self.in_queue = Queue()  # SpeciesArray from peers
        self.arrays_received: list[SpeciesArray] = []  # Accumulated arrivals

    def run(self) -> None:
        """Accumulate incoming individuals until None is received (shutdown signal)."""
        while True:
            species_arr = cast(SpeciesArray | None, self.in_queue.get())
            if species_arr is None:
                break
            if len(species_arr) > 0:
                self.arrays_received.append(species_arr)


class Incubator:
    """
    Central coordinator for genetic programming evolution.

    The Incubator orchestrates the complete evolutionary process:

    1. **Parallel Evaluation**: Distributes fitness evaluation across worker
       processes using multiprocessing for efficient computation.

    2. **Genetic Operators**: Applies selection, mutation, and crossover to
       create new generations of evolved programs.

    3. **Elite Migration**: Exchanges top-performing individuals with peer
       incubators for distributed evolution (via TransferSender/Receiver).

    4. **Hall of Fame**: Maintains best-ever individuals and periodically
       injects them back into the population.

    5. **Generation Management**: Coordinates the full evolution loop including
       evaluation, selection, reproduction, and replacement.

    Attributes:
        population: The evolving Population of Species instances
        random: Random number generator for stochastic operations
        id: Unique identifier for this incubator
        peers: Dictionary of connected peer incubators (for distributed evolution)

    Example:
        >>> population = MySpecies.spawn(n=100)
        >>> incubator = Incubator(population)
        >>> incubator.evolve(
        >>>     evaluator=my_evaluator,
        >>>     selection=TournamentSelection(tournament_size=3),
        >>>     n_gens=50,
        >>>     mutation_prob=0.7
        >>> )
    """

    def __init__(
        self,
        population: Population,
        peers: list[Self] | None = None,
        id: int | None = None,
    ) -> None:
        """
        Initialize an Incubator with a population.

        Args:
            population: Initial Population to evolve
            peers: Optional list of peer Incubators for distributed evolution
            id: Optional unique identifier (auto-generated if not provided)
        """
        self.random = Random()
        self.population = population
        self.id = id if id is not None else builtin_id(self)
        self.peers: dict[int, Self] = {p.id: p for p in (peers or [])}

        # Background threads for elite exchange with peers
        self._transfer_sender = TransferSender(self)
        self._transfer_receiver = TransferReceiver(self)

        # Queues for worker communication
        self._ctx_queue = Queue()  # Evaluator context updates
        self._population_queue = Queue()  # Population updates

        # Control flags for evolution loop
        self._stop_var = Value("b", False)
        self._pause_var = Value("b", False)
        self._max_workers = 0  # Number of worker processes

        # Adaptive mutation tracking
        self._fitness_history: list[float] = []  # Track best fitness per generation

    def update_evaluator_context(self, data: Any):
        self._ctx_queue.put(data)

    @property
    def is_paused(self) -> bool:
        return bool(self._pause_var.value)

    def stop(self):
        self._stop_var.value = True

    def pause(self):
        self._pause_var.value = True

    def unpause(self):
        self._pause_var.value = False

    def reset_population(self, new_pop: Population):
        self._population_queue.put(new_pop)

    def compute_adaptive_mutation_rate(
        self, i_gen: int, max_gen: int | None, base_rate: float = 0.7
    ) -> float:
        """Adapt mutation rate based on progress and stagnation.

        Strategy:
        - Early stage (0-30% gens): High mutation (0.8) for exploration
        - Mid stage (30-70% gens): Medium mutation (0.6)
        - Late stage (70-100% gens): Low mutation (0.4) for exploitation
        - Boost by +0.2 if no improvement detected (stagnation)

        Args:
            i_gen: Current generation index
            max_gen: Maximum generations (None = use base_rate)
            base_rate: Base mutation rate if max_gen is None

        Returns:
            Adaptive mutation rate in [0.4, 0.95]
        """
        if max_gen is None:
            return base_rate

        progress = i_gen / max_gen

        # Decrease mutation rate over time (exploration → exploitation)
        if progress < 0.3:
            stage_rate = 0.8
        elif progress < 0.7:
            stage_rate = 0.6
        else:
            stage_rate = 0.4

        # Detect stagnation (no improvement in last N generations)
        stagnation_window = min(20, max(5, max_gen // 10))
        if len(self._fitness_history) >= stagnation_window:
            recent_best = max(self._fitness_history[-stagnation_window:])
            current_best = self._fitness_history[-1] if self._fitness_history else float("-inf")

            # If stagnated, boost mutation for exploration
            if current_best <= recent_best:
                stage_rate = min(stage_rate + 0.2, 0.95)

        return stage_rate

    def incubate(
        self,
        evaluator: Evaluator,
        selection: SelectionAlgorithm | None = None,
        max_generations: int | None = None,
        mutation_rate: float = 0.5,
        max_workers: int | None = None,
        batch_size: int | None = None,
        callback: IncubatorCallback | Sequence[IncubatorCallback] | None = None,
        ctx: dict | None = None,
        population_size_strategy: "PopulationSizeStrategy | None" = None,
        **kwargs,
    ) -> Self:
        hof = self.population.hof
        gen = self.population.instances
        chromosomes = type(gen[0]).chromosomes
        ctx = dict(**evaluator.ctx, **(ctx or {}))

        # Initial offspring array (will be resized dynamically if strategy provided)
        offspring = np.empty(gen.size, dtype=object)
        mutation_rate = clamp(mutation_rate, 0, 1)
        max_workers = 1 if is_debug() else max(max_workers or os.cpu_count() or 1, 1)
        batch_size = max(batch_size or ceil(gen.size / max_workers), 1)
        callbacks = [x for x in flatten(callback) if x] if callback else []

        # Selection will be recreated each generation if pop size changes
        selection = selection or SelectionAlgorithm.default(
            pop_size=self.population.size, n_objectives=len(evaluator.weights)
        )

        if ctx:
            evaluator.ctx = ctx

        self._max_workers = max_workers
        self._stop_var.value = False

        for inst in cast(Sequence[Species], gen):
            inst.fitness.weights = tuple(evaluator.weights)

        # Use threads if debugging
        executor_factory = ThreadPoolExecutor if is_debug() else ProcessPoolExecutor

        # Shared counter to track worker initialization order
        worker_counter = Value('i', 0)

        create_pool = lambda evaluator, chromosomes: executor_factory(
            max_workers=max_workers,
            initializer=self.batch_evaluate_initializer,
            initargs=(evaluator, chromosomes, worker_counter),
        )

        i_gen = 0
        pool = create_pool(evaluator, chromosomes)

        logger.info(f"Starting evolution: pop_size={gen.size}, max_generations={max_generations}, mutation_rate={mutation_rate}")

        while True:
            # If paused, spinlock until resumed
            if self.is_paused:
                sleep(0.1)
                continue

            if not self._population_queue.empty():
                self.population = self._ctx_queue.get()
                hof = self.population.hof
                i_gen = 0
                for inst in cast(Sequence[Species], gen):
                    inst.fitness.weights = tuple(evaluator.weights)

            if not self._ctx_queue.empty():
                evaluator.ctx = self._ctx_queue.get()
                pool.shutdown(wait=False, cancel_futures=True)
                # Reset worker counter for new pool
                worker_counter.value = 0
                pool = create_pool(evaluator, chromosomes)

            for inst in gen:
                for tree in inst.trees.values():
                    del tree.chromosome

            # Evaluate the population concurrently
            species_batches = list(iter_batches(gen, batch_size))
            batches: list = [(i_gen, i, b) for i, b in enumerate(species_batches)]

            results = list(pool.map(self.batch_evaluate, batches))

            for inst in gen:
                inst.chromosomes = chromosomes
                for name, tree in inst.trees.items():
                    tree.chromosome = chromosomes[name]

            # Set fitness values returned on respective instances
            gen_evaluated = []
            for batch_index, evaled_instances in results:
                # for inst, values in zip(batch, fitness_values_batch):
                # inst.fitness.set_values(values)
                for inst in evaled_instances:
                    for name, tree in inst.trees.items():
                        tree.chromosome = chromosomes[name]
                    gen_evaluated.append(inst)

            # Sort evaluated individuals from high to low fitness and update the
            # hall-of-fame, taking the most fit from this generation.
            gen = np.array(gen_evaluated, dtype=object)

            # Update population instances so callbacks see the correct size
            self.population.instances = gen
            self.population.size = gen.size

            # Track this gen's leader. Sort is False bc we're already sorted
            hof.update(gen)

            # Track fitness history for adaptive mutation
            if hof.best:
                self._fitness_history.append(hof.best.fitness.values[0])

            # Log generation progress
            if hof.best:
                best_fitness = hof.best.fitness.values
                if len(best_fitness) == 1:
                    logger.info(f"Gen {i_gen:3d}: best_fitness={best_fitness[0]:.6f}, pop_size={gen.size}")
                else:
                    fitness_str = ", ".join([f"{v:.6f}" for v in best_fitness])
                    logger.info(f"Gen {i_gen:3d}: best_fitness=[{fitness_str}], pop_size={gen.size}")

            # Trigger any registered per-generation callbacks:
            for func in callbacks:
                try:
                    func(i_gen, self, ctx)
                except:
                    logger.exception(f"incubator callback {func.__name__} failed. stopping")
                    self.stop()

            # increment generation index
            i_gen += 1

            if i_gen == max_generations or self._stop_var.value:
                break

            if hof.best.fitness.values == hof.best.fitness.worst:
                # Completely regenerate the population
                self.population.replace()
                gen = self.population.instances
                for inst in cast(Sequence[Species], gen):
                    inst.fitness.weights = tuple(evaluator.weights)
            else:
                # Calculate target population size for next generation
                if population_size_strategy and max_generations:
                    next_size = population_size_strategy.get_size_for_generation(
                        i_gen, max_generations
                    )
                else:
                    next_size = gen.size

                # Recreate offspring array if size changed
                if next_size != offspring.size:
                    offspring = np.empty(next_size, dtype=object)

                # Perform cross-over, mutation, and elitism
                # Pass next_size to selection.select() to select correct number of parents
                parents = selection.select(gen, k=next_size)

                # Compute adaptive mutation rate based on progress and stagnation
                adaptive_mutation_rate = self.compute_adaptive_mutation_rate(
                    i_gen, max_generations, base_rate=mutation_rate
                )

                self.mutate_or_mate(parents, offspring, adaptive_mutation_rate)

                elite_injection_rounds = int(max(0.02 * offspring.size, 1))
                self.inject_elites_from_hof(offspring, hof, elite_injection_rounds)
                self.inject_species_received_from_transfers(offspring)

                # Shuffle the next generation to ensure injected individuals are
                # randomly distributed, not concentrated in the tail.
                np.random.shuffle(offspring)

                # Replace population with next generation
                self.population.instances = gen = offspring
                self.population.size = offspring.size

        logger.info(f"Evolution complete after {i_gen} generations")
        if hof.best:
            logger.info(f"Best fitness achieved: {hof.best.fitness.values}")

        return self

    def inject_elites_from_hof(self, pop: SpeciesArray, hof: HallOfFame, rounds: int = 1):
        if len(hof) == 0:
            return

        # Randomly inject past performers
        for i in range(1, rounds + 1):
            if self.random.flip(p=0.5):
                leader_idx = int(
                    clamp(
                        round(self.random.decay(0, len(hof), rate=5)),
                        0,
                        len(hof) - 1,
                    )
                )
                pop[len(pop) - i] = hof[leader_idx].copy(copy_fitness=True)

    def inject_species_received_from_transfers(self, offspring: SpeciesArray):
        if not self._transfer_receiver.is_alive:
            self._transfer_receiver.start()
        # Inject species received from other incubators.
        # Horizontal Gene Transfer
        if self._transfer_receiver.arrays_received:
            while self._transfer_receiver.arrays_received:
                arr = self._transfer_receiver.arrays_received.pop()
                for species in arr:
                    offspring[self.random.randrange(0, offspring.size)] = species

    def transfer(self, recipient: Self, n: int) -> None:
        if not self._transfer_sender.is_alive:
            self._transfer_sender.start()
        self._transfer_sender.in_queue.put((recipient.id, n))

    def mutate_or_mate(
        self,
        parents: SpeciesArray,
        offspring: SpeciesArray,
        mutation_prob: float,
    ) -> None:
        i_child = 0
        pop = self.population
        random = self.random

        while i_child < offspring.size:
            # offspring[i_child] = parents[i_child].copy()
            # i_child += 1
            # continue

            # Try to generate a child via mutation
            if random.flip(p=mutation_prob):
                child = cast(Species, random.np_choice(parents)).copy()
                if child.mutate():
                    offspring[i_child] = child
                    i_child += 1
                    continue

            # Generate a child via crossover. Take the fist child
            pair = random.np_choice(parents, 2, replace=False)

            mother, father = cast(Sequence[Species], pair)

            child = father.mate(mother)
            if child:
                offspring[i_child] = child
                i_child += 1

            if self.random.flip() and i_child < offspring.size:
                child = mother.mate(father)
                if child:
                    offspring[i_child] = child
                    i_child += 1

    @classmethod
    def batch_evaluate(cls, args: tuple[int, int, SpeciesArray]) -> tuple[int, Sequence[Species]]:

        i_gen, batch_index, instances = args
        values_batches = []  # output batches of fitness value tuples
        evaluator: Evaluator = globals()["evaluator"]
        chromosomes = globals()["chromosomes"]

        if not evaluator.is_ready:
            evaluator.setup()

        evaluator.on_batch_received(instances, i_gen)

        # Eval fitness of each individual in batch
        for inst in cast(Sequence[Species], instances):
            del inst.fitness.values

            for name, tree in inst.trees.items():
                tree.chromosome = chromosomes[name]

            inst.compile()

            try:
                inst.fitness.set_values(evaluator.evaluate(inst, i_gen=i_gen))
                values_batches.append(inst)
            except:
                logger.exception("instance failed to compile and run")
                inst.fitness.set_values(inst.fitness.worst)
                values_batches.append(inst)
                if is_debug():
                    breakpoint()

            for tree in inst.trees.values():
                del tree.chromosome

        evaluator.on_batch_evaluated(instances, i_gen)

        return (batch_index, values_batches)

    @staticmethod
    def batch_evaluate_initializer(evaluator: Evaluator, chromosomes: dict, worker_counter: Synchronized[int]):
        globals()["evaluator"] = evaluator
        globals()["chromosomes"] = chromosomes

        # Mark first worker for digest printing
        with worker_counter.get_lock():
            worker_id = worker_counter.value
            worker_counter.value += 1

        globals()["is_first_worker"] = (worker_id == 0)


