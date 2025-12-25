"""
These functions implement NSGA2 and 3. They're lifted from py-deap. The
nondominated sorting methods have been optimized by using numpy instead of
native python list operations.
"""

from itertools import chain
from operator import attrgetter
from typing import Sequence, cast
import numpy as np
from collections import defaultdict

from nature.species import Species
from nature.typing import SpeciesArray


def sel_NSGA2(individuals: SpeciesArray, k: int, nd="standard") -> SpeciesArray:
    """Apply NSGA-II selection operator on the *individuals*. Usually, the
    size of *individuals* will be larger than *k* because any individual
    present in *individuals* will appear in the returned list at most once.
    Having the size of *individuals* equals to *k* will have no effect other
    than sorting the population according to their front rank. The
    list returned contains references to the input *individuals*. For more
    details on the NSGA-II operator see [Deb2002]_.

    :param individuals: A list of individuals to select from.
    :param k: The number of individuals to select.
    :param nd: Specify the non-dominated algorithm to use: 'standard' or 'log'.
    :returns: A list of selected individuals.

    .. [Deb2002] Deb, Pratab, Agarwal, and Meyarivan, "A fast elitist
       non-dominated sorting genetic algorithm for multi-objective
       optimization: NSGA-II", 2002.
    """
    if nd == "standard":
        pareto_fronts = sort_nondominated(individuals, k)
    elif nd == "log":
        pareto_fronts = sort_log_nondominated(individuals, k)
    else:
        raise Exception(
            "selNSGA2: The choice of non-dominated sorting " 'method "{0}" is invalid.'.format(nd)
        )

    for front in pareto_fronts:
        assign_crowding_distance(front)

    chosen = list(chain(*pareto_fronts[:-1]))
    k = k - len(chosen)
    if k > 0:
        sorted_front = sorted(
            pareto_fronts[-1], key=attrgetter("fitness.crowding_dist"), reverse=True
        )
        chosen.extend(sorted_front[:k])

    return np.array(chosen, dtype=object)


def assign_crowding_distance(instances: SpeciesArray):
    """Assign a crowding distance to each individual's fitness using vectorized operations."""
    if len(instances) == 0:
        return

    # Extract fitness values into a NumPy array for efficient manipulation
    fitness_values = np.array([ind.fitness.values for ind in instances])
    num_individuals = len(instances)
    num_objectives = fitness_values.shape[1]

    # Initialize distances array
    distances = np.zeros(num_individuals)

    # Iterate over each objective
    for i in range(num_objectives):
        # Sort the fitness values for the current objective (sorting by column i)
        sorted_indices = np.argsort(fitness_values[:, i])
        sorted_values = fitness_values[sorted_indices, i]

        # Assign extreme values for the first and last individuals
        distances[sorted_indices[0]] = float("inf")
        distances[sorted_indices[-1]] = float("inf")

        # Skip if the first and last values are the same (no range for crowding distance)
        if sorted_values[-1] == sorted_values[0]:
            continue

        # Normalize the crowding distance
        norm = float(sorted_values[-1] - sorted_values[0])

        # Calculate the crowding distance for the rest of the individuals
        for j in range(1, num_individuals - 1):
            cur_idx = sorted_indices[j]
            distances[cur_idx] += (sorted_values[j + 1] - sorted_values[j - 1]) / norm

    # Assign the crowding distances to the individuals' fitness attribute
    for i, dist in enumerate(distances):
        instances[i].fitness.crowding_dist = dist


def sel_NSGA3(
    instances: SpeciesArray,
    k: int,
    ref_points,
    nd="log",
    best_point=None,
    worst_point=None,
    extreme_points=None,
) -> SpeciesArray:
    """Implementation of NSGA-III selection as presented in [Deb2014]_.

    This implementation is partly based on `lmarti/nsgaiii
    <https://github.com/lmarti/nsgaiii>`_. It departs slightly from the
    original implementation in that it does not use memory to keep track
    of ideal and extreme points. This choice has been made to fit the
    functional api of DEAP. For a version of NSGA-III see
    :class:`~deap.tools.selNSGA3WithMemory`.

    :param individuals: A list of individuals to select from.
    :param k: The number of individuals to select.
    :param ref_points: Reference points to use for niching.
    :param nd: Specify the non-dominated algorithm to use: 'standard' or 'log'.
    :param best_point: Best point found at previous generation. If not provided
        find the best point only from current individuals.
    :param worst_point: Worst point found at previous generation. If not provided
        find the worst point only from current individuals.
    :param extreme_points: Extreme points found at previous generation. If not provided
        find the extreme points only from current individuals.
    :returns: A list of selected individuals.
    :returns: If `return_memory` is :data:`True`, a namedtuple with the
        `best_point`, `worst_point`, and `extreme_points`.


    You can generate the reference points using the :func:`uniform_reference_points`
    function::

        >>> ref_points = tools.uniform_reference_points(nobj=3, p=12)   # doctest: +SKIP
        >>> selected = selNSGA3(population, k, ref_points)              # doctest: +SKIP

    .. [Deb2014] Deb, K., & Jain, H. (2014). An Evolutionary Many-Objective Optimization
        Algorithm Using Reference-Point-Based Nondominated Sorting Approach,
        Part I: Solving Problems With Box Constraints. IEEE Transactions on
        Evolutionary Computation, 18(4), 577-601. doi:10.1109/TEVC.2013.2281535.
    """
    if nd == "standard":
        pareto_fronts = sort_nondominated(instances, k)
    elif nd == "log":
        pareto_fronts = sort_log_nondominated(instances, k)
    else:
        raise Exception(
            "selNSGA3: The choice of non-dominated sorting " "method '{0}' is invalid.".format(nd)
        )

    # Extract fitnesses as a numpy array in the nd-sort order
    # Use wvalues * -1 to tackle always as a minimization problem
    fitnesses = np.array([ind.fitness.wvalues for f in pareto_fronts for ind in f])
    fitnesses *= -1

    # Get best and worst point of population, contrary to pymoo
    # we don't use memory
    if best_point is not None and worst_point is not None:
        best_point = np.min(np.concatenate((fitnesses, best_point), axis=0), axis=0)
        worst_point = np.max(np.concatenate((fitnesses, worst_point), axis=0), axis=0)
    else:
        best_point = np.min(fitnesses, axis=0)
        worst_point = np.max(fitnesses, axis=0)

    extreme_points = find_extreme_points(fitnesses, best_point, extreme_points)
    front_worst = np.max(fitnesses[: sum(len(f) for f in pareto_fronts), :], axis=0)
    intercepts = find_intercepts(extreme_points, best_point, worst_point, front_worst)
    niches, dist = associate_to_niche(fitnesses, ref_points, best_point, intercepts)

    # Get counts per niche for individuals in all front but the last
    niche_counts = np.zeros(len(ref_points), dtype=np.int64)
    index, counts = np.unique(niches[: -len(pareto_fronts[-1])], return_counts=True)
    niche_counts[index] = counts

    # Choose individuals from all fronts but the last
    chosen = list(chain(*pareto_fronts[:-1]))

    # Use niching to select the remaining individuals
    sel_count = len(chosen)
    n = k - sel_count
    selected = niching(pareto_fronts[-1], n, niches[sel_count:], dist[sel_count:], niche_counts)
    chosen.extend(selected)

    return np.array(chosen, dtype=object)


def find_extreme_points(fitnesses, best_point, extreme_points=None):
    "Finds the individuals with extreme values for each objective function."
    # Keep track of last generation extreme points
    if extreme_points is not None:
        fitnesses = np.concatenate((fitnesses, extreme_points), axis=0)

    # Translate objectives
    ft = fitnesses - best_point

    # Find achievement scalarizing function (asf)
    asf = np.eye(best_point.shape[0])
    asf[asf == 0] = 1e6
    asf = np.max(ft * asf[:, np.newaxis, :], axis=2)

    # Extreme point are the fitnesses with minimal asf
    min_asf_idx = np.argmin(asf, axis=1)
    return fitnesses[min_asf_idx, :]


def find_intercepts(extreme_points, best_point, current_worst, front_worst):
    """Find intercepts between the hyperplane and each axis with
    the ideal point as origin."""
    # Construct hyperplane sum(f_i^n) = 1
    b = np.ones(extreme_points.shape[1])
    A = extreme_points - best_point
    try:
        x = np.linalg.solve(A, b)
    except np.linalg.LinAlgError:
        intercepts = current_worst
    else:
        if np.count_nonzero(x) != len(x):
            intercepts = front_worst
        else:
            intercepts = 1 / x

            if (
                not np.allclose(np.dot(A, x), b)
                or np.any(intercepts <= 1e-6)
                or np.any((intercepts + best_point) > current_worst)
            ):
                intercepts = front_worst

    return intercepts


def associate_to_niche(fitnesses, reference_points, best_point, intercepts):
    """Associates individuals to reference points and calculates niche number.
    Corresponds to Algorithm 3 of Deb & Jain (2014)."""
    # Normalize by ideal point and intercepts
    fn = (fitnesses - best_point) / (intercepts - best_point + np.finfo(float).eps)

    # Create distance matrix
    fn = np.repeat(np.expand_dims(fn, axis=1), len(reference_points), axis=1)
    norm = np.linalg.norm(reference_points, axis=1)

    distances = np.sum(fn * reference_points, axis=2) / norm.reshape(1, -1)
    distances = (
        distances[:, :, np.newaxis]
        * reference_points[np.newaxis, :, :]
        / norm[np.newaxis, :, np.newaxis]
    )
    distances = np.linalg.norm(distances - fn, axis=2)

    # Retrieve min distance niche index
    niches = np.argmin(distances, axis=1)
    distances = distances[list(range(niches.shape[0])), niches]
    return niches, distances


def niching(individuals, k, niches, distances, niche_counts):
    selected = []
    available = np.ones(len(individuals), dtype=bool)
    while len(selected) < k:
        # Maximum number of individuals (niches) to select in that round
        n = k - len(selected)

        # Find the available niches and the minimum niche count in them
        available_niches = np.zeros(len(niche_counts), dtype=bool)
        available_niches[np.unique(niches[available])] = True
        min_count = np.min(niche_counts[available_niches])

        # Select at most n niches with the minimum count
        selected_niches = np.flatnonzero(
            np.logical_and(available_niches, niche_counts == min_count)
        )
        np.random.shuffle(selected_niches)
        selected_niches = selected_niches[:n]

        for niche in selected_niches:
            # Select from available individuals in niche
            niche_individuals = np.flatnonzero(np.logical_and(niches == niche, available))
            np.random.shuffle(niche_individuals)

            # If no individual in that niche, select the closest to reference
            # Else select randomly
            if niche_counts[niche] == 0:
                sel_index = niche_individuals[np.argmin(distances[niche_individuals])]
            else:
                sel_index = niche_individuals[0]

            # Update availability, counts and selection
            available[sel_index] = False
            niche_counts[niche] += 1
            selected.append(individuals[sel_index])

    return selected


def sort_nondominated(instances: SpeciesArray, k: int, first_front_only=False) -> SpeciesArray:
    """Sort the first *k* *individuals* into different nondomination levels
    using the Fast Nondominated Sorting Algorithm."""

    if k == 0:
        return np.empty(0, dtype=object)

    # Get the fitness values of the individuals as a NumPy array
    fits = np.array([x.fitness for x in cast(Sequence[Species], instances)])

    # Prepare the domination matrix using broadcasting
    dominates = np.zeros((len(fits), len(fits)), dtype=bool)

    # Compare each individual against each other (vectorized comparison)
    for i in range(len(fits)):
        for j in range(i + 1, len(fits)):
            dominates[i, j] = fits[i].dominates(fits[j])
            dominates[j, i] = fits[j].dominates(fits[i])

    # Compute the dominance counts and dominated individuals for each individual
    domination_count = np.sum(dominates, axis=1)

    # Initialize the first Pareto front
    current_front = cast(list[bool], np.where(domination_count == 0)[0].tolist())
    fronts = [current_front]
    pareto_sorted = len(current_front)

    # Dominance count adjustment and front sorting loop
    if not first_front_only:
        N = min(len(instances), k)
        while pareto_sorted < N:
            next_front = []
            for i in current_front:
                for j in range(len(fits)):
                    if dominates[i, j]:
                        domination_count[j] -= 1
                        if domination_count[j] == 0:
                            next_front.append(j)
                            pareto_sorted += 1
            fronts.append(next_front)
            current_front = next_front

    # Convert indices back to individuals
    sorted_fronts = np.fromiter(
        ([instances[idx] for idx in front] for front in fronts),
        dtype=object,
        count=len(fronts),
    )

    return sorted_fronts


def sort_log_nondominated(instances: SpeciesArray, k: int, first_front_only=False) -> SpeciesArray:
    """Sort *individuals* in pareto non-dominated fronts using the Generalized
    Reduced Run-Time Complexity Non-Dominated Sorting Algorithm presented by
    Fortin et al. (2013).
    """
    if k == 0:
        return np.empty(0, dtype=object)

    # Get the fitness values as a NumPy array (assuming individuals have a 'fitness' attribute)
    fitnesses = np.array([ind.fitness.wvalues for ind in instances])

    # Initialize dominance count and dominance matrix
    num_individuals = len(instances)
    dominance_count = np.zeros(num_individuals, dtype=int)
    dominates = np.zeros((num_individuals, num_individuals), dtype=bool)

    # Compare all pairs of individuals
    for i in range(num_individuals):
        for j in range(i + 1, num_individuals):
            # Check if i dominates j
            if np.all(fitnesses[i] >= fitnesses[j]) and np.any(fitnesses[i] > fitnesses[j]):
                dominates[i, j] = True
                dominance_count[j] += 1
            # Check if j dominates i
            elif np.all(fitnesses[j] >= fitnesses[i]) and np.any(fitnesses[j] > fitnesses[i]):
                dominates[j, i] = True
                dominance_count[i] += 1

    # Sorting individuals into Pareto fronts
    fronts = defaultdict(list)
    current_front = np.where(dominance_count == 0)[0]  # Individuals not dominated by any other
    fronts[0] = list(current_front)

    # Sort the rest of the individuals into subsequent fronts
    pareto_sorted = len(current_front)
    if not first_front_only:
        next_front = []
        while pareto_sorted < k:
            for i in current_front:
                # For each individual in the current front, find individuals it dominates
                dominated_individuals = np.where(dominates[i] == 1)[0]
                for j in dominated_individuals:
                    dominance_count[j] -= 1
                    if dominance_count[j] == 0:
                        next_front.append(j)
                        pareto_sorted += 1
            current_front = next_front
            fronts[len(fronts)] = next_front
            next_front = []

    # Return the Pareto fronts as lists of individuals
    sorted_fronts = np.fromiter(
        ([instances[idx] for idx in front] for front in fronts.values()),
        dtype=object,
        count=len(fronts),
    )

    return sorted_fronts[:k] if not first_front_only else sorted_fronts[0]
