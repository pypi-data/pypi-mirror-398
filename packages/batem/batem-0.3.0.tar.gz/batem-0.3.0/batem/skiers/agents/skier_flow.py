from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional
import random
from datetime import datetime, timedelta

from batem.skiers.plot.agents import IndividualSkierPlotter
from batem.skiers.plot.skier import SimulationStatePlotter


class SkierType(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"


class SkierPreference(Enum):
    SPEED = "speed"  # Prefers faster routes
    SCENIC = "scenic"  # Prefers scenic routes
    CHALLENGE = "challenge"  # Prefers difficult routes


@dataclass
class SkiliftState:
    """Represents the current state of a skilift."""
    name: str
    capacity: int
    current_queue: int
    wait_time: float  # in minutes
    difficulty: str  # easy, intermediate, expert
    is_open: bool = True
    skiers_in_lift: int = 0  # Number of skiers currently in the lift
    cycle_time: int = 20  # Time in minutes for a full cycle of the lift


class SkierAgent:
    """Represents a skier agent in the system."""

    def __init__(self,
                 skier_type: SkierType,
                 preference: SkierPreference,
                 patience: float = 0.5):  # 0-1 scale
        self.skier_type = skier_type
        self.preference = preference
        self.patience = patience
        self.current_skilift: Optional[str] = None
        self.trajectory: List[str] = []
        self.start_time: Optional[datetime] = None
        self.total_wait_time: float = 0.0
        self.time_in_lift: float = 0.0  # Time spent in current lift
        self.is_in_lift: bool = False  # Whether skier is currently in lift
        self.is_in_queue: bool = False  # Whether skier is currently in a queue

    def choose_next_skilift(self,
                            available_skilifts: Dict[str, SkiliftState]
                            ) -> str:
        """Choose the next skilift based on preferences and current state."""
        if not available_skilifts:
            return None

        # Filter skilifts based on skier type and difficulty
        suitable_skilifts = {
            name: state for name, state in available_skilifts.items()
            if state.is_open and self._is_suitable_difficulty(state.difficulty)
        }

        if not suitable_skilifts:
            return None

        # Score each skilift based on preferences
        scores = {}
        for name, state in suitable_skilifts.items():
            score = 0

            # Speed preference: prioritize shorter wait times
            if self.preference == SkierPreference.SPEED:
                score += 1.0 / (state.wait_time + 1)

            # Scenic preference: prioritize less crowded lifts
            elif self.preference == SkierPreference.SCENIC:
                score += 1.0 / (state.current_queue + 1)

            # Challenge preference: prioritize more difficult routes
            elif self.preference == SkierPreference.CHALLENGE:
                score += self._difficulty_score(state.difficulty)

            # Add some randomness to prevent all agents choosing the same lift
            score *= random.uniform(0.8, 1.2)

            scores[name] = score

        # Choose skilift with highest score
        return max(scores.items(), key=lambda x: x[1])[0]

    def _is_suitable_difficulty(self, difficulty: str) -> bool:
        """Check if the difficulty level is suitable for the skier type."""
        if self.skier_type == SkierType.BEGINNER:
            return difficulty == "easy"
        elif self.skier_type == SkierType.INTERMEDIATE:
            return difficulty in ["easy", "intermediate"]
        else:  # EXPERT
            return True

    def _difficulty_score(self, difficulty: str) -> float:
        """Calculate score based on difficulty level."""
        return {
            "easy": 0.3,
            "intermediate": 0.6,
            "expert": 1.0
        }.get(difficulty, 0.0)

    def should_wait(self, wait_time: float) -> bool:
        """Decide whether to wait in queue based on patience."""
        max_wait = 30 * (1 - self.patience)  # Max wait time in minutes
        return wait_time <= max_wait


class RandomAgent(SkierAgent):
    """A skier agent that chooses a random skilift."""

    def choose_next_skilift(self, available_skilifts: Dict[str, SkiliftState]) -> str:
        """Choose a random skilift from the available skilifts."""
        return random.choice(list(available_skilifts.keys()))


class SkierFlowSimulator:
    """Simulates skier flow through the resort."""

    def __init__(self,
                 skilifts: Dict[str, SkiliftState],
                 time_step: int = 5):  # minutes
        self.skilifts = skilifts
        self.time_step = time_step
        self.current_time = datetime(2023, 2, 16, 8, 0, 0)
        self.skiers: List[SkierAgent] = []
        self.history: List[Dict] = []

    def add_skier(self, skier: SkierAgent):
        """Add a new skier to the simulation."""
        skier.start_time = self.current_time
        self.skiers.append(skier)

    def update_skilift_states(self):
        """Update the state of all skilifts."""
        for skilift in self.skilifts.values():
            if not skilift.is_open:
                continue

            # Calculate how many skiers can be processed this time step
            skiers_per_minute = skilift.capacity / skilift.cycle_time
            skiers_to_process = int(skiers_per_minute * self.time_step)

            # First, process skiers leaving the lift
            skiers_leaving = min(skiers_to_process, skilift.skiers_in_lift)
            skilift.skiers_in_lift -= skiers_leaving

            # Then, process skiers joining the lift
            available_capacity = skilift.capacity - skilift.skiers_in_lift
            skiers_joining = min(
                skiers_to_process - skiers_leaving,  # Remaining processing capacity
                skilift.current_queue,
                available_capacity
            )

            # Update queue and lift
            skilift.current_queue -= skiers_joining
            skilift.skiers_in_lift += skiers_joining

            # Update wait time based on queue length and processing rate
            if skiers_per_minute > 0:
                skilift.wait_time = (skilift.current_queue / skiers_per_minute)
            else:
                skilift.wait_time = 0

    def step(self):
        """Advance the simulation by one time step."""
        # Update skilift states
        self.update_skilift_states()

        # Update each skier
        for skier in self.skiers:
            if skier.is_in_lift:
                # Update time spent in lift
                skier.time_in_lift += self.time_step

                # Check if skier has completed lift cycle
                current_lift = self.skilifts[skier.current_skilift]
                if skier.time_in_lift >= current_lift.cycle_time:
                    # Skier exits lift
                    skier.is_in_lift = False
                    skier.time_in_lift = 0
                    current_lift.skiers_in_lift -= 1
                    skier.current_skilift = None
            elif not skier.current_skilift and not skier.is_in_queue:
                # Choose next skilift
                next_skilift = skier.choose_next_skilift(self.skilifts)
                if next_skilift:
                    skier.current_skilift = next_skilift
                    skier.is_in_queue = True
                    self.skilifts[next_skilift].current_queue += 1
                    skier.trajectory.append(next_skilift)
            elif skier.is_in_queue:
                # Check if skier should wait or move on
                current_state = self.skilifts[skier.current_skilift]

                # Add some randomness to the decision to make it more realistic
                if not skier.should_wait(current_state.wait_time):
                    # Only leave with a certain probability based on wait time
                    leave_probability = min(
                        1.0, current_state.wait_time / 30.0)
                    if random.random() < leave_probability:
                        skier.current_skilift = None
                        skier.is_in_queue = False
                        current_state.current_queue -= 1
                else:
                    skier.total_wait_time += self.time_step

        # Record state
        self._record_state()

        # Advance time
        self.current_time += timedelta(minutes=self.time_step)

    def _record_state(self):
        """Record the current state of the simulation."""
        state = {
            'timestamp': self.current_time,
            'skilift_states': {
                name: {
                    'queue': skilift_state.current_queue,
                    'wait_time': skilift_state.wait_time,
                    'skiers_in_lift': skilift_state.skiers_in_lift,
                    'capacity': skilift_state.capacity
                }
                for name, skilift_state in self.skilifts.items()
            },
            'active_skiers': len(self.skiers)
        }
        self.history.append(state)

    def get_statistics(self) -> Dict:
        """Get statistics about the simulation."""
        return {
            'total_skiers': len(self.skiers),
            'average_wait_time': sum(s.total_wait_time for s in self.skiers) /
            len(self.skiers) if self.skiers else 0,
            'most_crowded_lift': max(
                self.skilifts.items(),
                key=lambda x: x[1].current_queue
            )[0] if self.skilifts else None,
            'total_simulation_time': (
                self.current_time - self.skiers[0].start_time
            ).total_seconds() / 60 if self.skiers else 0
        }


# Example usage
def run_simulation(skier_count: int = 200,
                   capacity_1: int = 30,
                   capacity_2: int = 30,
                   capacity_3: int = 30,
                   random_agent: bool = False,
                   step_count: int = 100):

    # python batem/skiers/agents/skier_flow.py

    # Initialize skilifts
    skilifts = {
        'Lift A': SkiliftState('Lift A', capacity=capacity_1, current_queue=0,
                               wait_time=0, difficulty='easy'),
        'Lift B': SkiliftState('Lift B', capacity=capacity_2, current_queue=0,
                               wait_time=0, difficulty='intermediate'),
        'Lift C': SkiliftState('Lift C', capacity=capacity_3, current_queue=0,
                               wait_time=0, difficulty='expert')
    }

    # Create simulator
    simulator = SkierFlowSimulator(skilifts)

    # Add skiers with different preferences
    for _ in range(skier_count):
        skier_type = random.choice(list(SkierType))
        preference = random.choice(list(SkierPreference))
        patience = random.random()
        if random_agent:
            skier = RandomAgent(skier_type, preference, patience)
        else:
            skier = SkierAgent(skier_type, preference, patience)
        simulator.add_skier(skier)

    # Run simulation for 100 time steps
    for _ in range(step_count):
        simulator.step()

    # Print statistics
    stats = simulator.get_statistics()
    print("Simulation Statistics:")
    print(f"Total Skiers: {stats['total_skiers']}")
    print(f"Average Wait Time: {stats['average_wait_time']:.2f} minutes")
    print(f"Most Crowded Lift: {stats['most_crowded_lift']}")
    print(
        f"Total Simulation Time: {stats['total_simulation_time']:.2f} minutes")

    # After running your simulation
    plotter = SimulationStatePlotter(simulator.history)

    # Plot individual metrics
    # plotter.plot_queue_lengths()
    plotter.plot_wait_times()
    # plotter.plot_active_skiers()
    plotter.plot_fill_rates()

    # Or plot all metrics together
    # plotter.plot_all_metrics()

    # Create plotter with your skier agents
    plotter = IndividualSkierPlotter(simulator.skiers)

    # Plot individual skier trajectory
    plotter.plot_skier_trajectory(0)  # Plot first skier

    # Plot metrics for top 10 skiers
    plotter.plot_skier_metrics(10)


if __name__ == "__main__":
    run_simulation()
