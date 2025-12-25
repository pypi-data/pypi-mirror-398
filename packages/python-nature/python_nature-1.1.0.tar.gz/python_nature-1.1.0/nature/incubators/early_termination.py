"""
Early Success Termination for Genetic Evolution.

Provides graceful early stopping when a valid solution is found and
no subsequent improvement is observed within a specified time window.
"""

from nature.logging import logger


class EarlySuccessTerminator:
    """
    Tracks success and determines when to terminate evolution gracefully.

    This class implements adaptive early termination logic:
    - Monitors for valid solutions (either at any time, or within a specified early phase)
    - Once found, tracks fitness improvements over the remaining evolution time
    - Terminates early if no improvement after M% of the REMAINING time has passed
    - Maintains validity of the solution (graceful termination, not failure)

    Example:
        terminator = EarlySuccessTerminator(early_phase_pct=None, improvement_window_pct=0.6)
        for gen in range(max_gen):
            # ... evolve population ...
            is_valid = check_solution_validity(best)
            if terminator.check_termination(gen, max_gen, best.fitness.values, is_valid):
                break  # Graceful early termination

    Attributes:
        early_phase_pct: Fraction of total generations considered "early phase", or None for "any time"
        improvement_window_pct: Fraction of remaining time to wait for improvement (default 0.6 = 60%)
        found_valid_solution: Whether a valid solution was found
        generation_found: Generation number where valid solution was first found
        best_fitness_at_find: Best fitness values observed since finding the solution
        generations_since_improvement: Counter for consecutive generations without improvement
        improvement_window_generations: Number of consecutive generations without improvement to tolerate
    """

    def __init__(
        self,
        early_phase_pct: float | None = None,
        improvement_window_pct: float = 0.6,
    ):
        """
        Initialize the early success terminator.

        Args:
            early_phase_pct: Fraction of total generations considered "early phase" (0.0-1.0),
                           or None to track valid solutions found at ANY point in evolution
            improvement_window_pct: Fraction of remaining time to wait for improvement (0.0-1.0)
                                  This is interpreted as the fraction of remaining generations
                                  to tolerate without improvement before terminating.
        """
        if early_phase_pct is not None and not 0.0 < early_phase_pct < 1.0:
            raise ValueError(f"early_phase_pct must be in (0, 1) or None, got {early_phase_pct}")
        if not 0.0 < improvement_window_pct < 1.0:
            raise ValueError(
                f"improvement_window_pct must be in (0, 1), got {improvement_window_pct}"
            )

        self.early_phase_pct = early_phase_pct
        self.improvement_window_pct = improvement_window_pct
        self.found_valid_solution = False
        self.generation_found: int | None = None
        self.best_fitness_at_find: tuple | None = None
        self.generations_since_improvement: int = 0
        self.improvement_window_generations: int | None = None

    def reset(self):
        """Reset the tracker for a new evolution run."""
        self.found_valid_solution = False
        self.generation_found = None
        self.best_fitness_at_find = None
        self.generations_since_improvement = 0
        self.improvement_window_generations = None

    def check_termination(
        self,
        current_generation: int,
        max_generations: int,
        current_fitness: tuple,
        is_valid_solution: bool,
    ) -> bool:
        """
        Check if evolution should terminate early.

        Logic:
        1. Detection phase:
           - If early_phase_pct is None: Track valid solutions at ANY generation
           - If early_phase_pct is set: Only track valid solutions within early phase
        2. Monitoring phase (after finding a valid solution):
           - Count consecutive generations without fitness improvement
           - Terminate if no improvement for M% of remaining generations
           - Reset counter whenever fitness improves

        Args:
            current_generation: Current generation number (0-indexed)
            max_generations: Maximum number of generations
            current_fitness: Current best fitness values (tuple for multi-objective)
            is_valid_solution: Whether the current solution meets validity criteria

        Returns:
            True if evolution should terminate early (gracefully), False otherwise

        Example:
            For max_gen=50, early_phase_pct=None, improvement_window_pct=0.6:
            - Solution found at gen 0
            - Remaining gens = 50 - 0 = 50
            - Improvement window = int(50 * 0.6) = 30 generations
            - If no improvement for 30 consecutive generations, terminate
            - Continuous improvements reset the counter
        """
        # Phase 1: Detect valid solutions
        if not self.found_valid_solution:
            # Check if we should track this generation based on early_phase_pct
            if self.early_phase_pct is None:
                # Track valid solutions at any generation
                can_track = True
            else:
                # Only track within early phase
                early_phase_threshold = max_generations * self.early_phase_pct
                can_track = current_generation <= early_phase_threshold

            if can_track and is_valid_solution:
                self.found_valid_solution = True
                self.generation_found = current_generation
                self.best_fitness_at_find = current_fitness
                self.generations_since_improvement = 0

                # Calculate how many consecutive generations without improvement to tolerate
                remaining_gens = max_generations - current_generation
                self.improvement_window_generations = int(
                    remaining_gens * self.improvement_window_pct
                )

                if self.early_phase_pct is None:
                    logger.info(
                        f"Valid solution found at gen {current_generation}/{max_generations}. "
                        f"Will terminate if no improvement for {self.improvement_window_generations} consecutive generations."
                    )
                else:
                    logger.info(
                        f"Valid solution found in early phase at gen {current_generation}/{max_generations}. "
                        f"Will terminate if no improvement for {self.improvement_window_generations} consecutive generations."
                    )
            return False

        # Phase 2: Monitor for improvement after finding valid solution
        # These should never be None here since we're in Phase 2, but add explicit checks for type safety
        if self.best_fitness_at_find is None or self.improvement_window_generations is None:
            # Should never happen, but handle gracefully
            logger.warning("Early terminator in invalid state - resetting")
            self.reset()
            return False

        # Check if fitness improved
        if current_fitness > self.best_fitness_at_find:
            # Improvement detected - reset counter and update best
            self.best_fitness_at_find = current_fitness
            self.generations_since_improvement = 0
            return False
        else:
            # No improvement - increment counter
            self.generations_since_improvement += 1

            # Check if we've exceeded the improvement window
            if self.generations_since_improvement >= self.improvement_window_generations:
                # No improvement for too long - graceful termination
                logger.info(
                    f"Early success termination at gen {current_generation}/{max_generations}. "
                    f"Valid solution found at gen {self.generation_found}, no improvement for "
                    f"{self.generations_since_improvement} consecutive generations "
                    f"({self.improvement_window_pct*100:.0f}% of remaining time)."
                )
                return True

            return False
