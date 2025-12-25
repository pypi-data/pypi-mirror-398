"""
Manager models for energy system control.

This module provides abstract and concrete implementations of energy
system managers that control and optimize energy distribution between
PV production and member consumption.
"""

from abc import ABC, abstractmethod
from batem.reno.pv.model import PVPlant
from batem.reno.simulation.member.model import Member
from batem.reno.simulation.recommendation import (
    Recommendation, RecommendationType)
from datetime import datetime

from batem.reno.utils import TimeSpaceHandler


class Manager(ABC):
    """
    Abstract base class for energy system managers.

    This class defines the interface for energy system managers that
    control and optimize energy distribution between PV production and
    member consumption.

    Attributes:
        time_space_handler: Handler for time and space operations
        recommendations: Dictionary mapping timestamps to recommendations
    """

    def __init__(self, time_space_handler: TimeSpaceHandler,
                 recommendation_interval: list[int]):
        """
        Initialize a new manager.

        Args:
            time_space_handler: Handler for time and space operations
            recommendation_interval: Interval of the day
            when recommendations are valid
        """
        self.time_space_handler = time_space_handler
        self.recommendation_interval = recommendation_interval
        self.recommendations: dict[datetime, Recommendation] = {}

    @abstractmethod
    def step(self,
             k: int,
             members: list[Member],
             pv: PVPlant) -> Recommendation:
        """
        Run a single step of the manager's control logic.

        Args:
            k: Time step index
            members: List of energy community members
            pv: PV plant instance

        Returns:
            Recommendation: Generated recommendation for this time step

        Example:
            >>> recommendation = manager.step(0, members, pv_plant)
        """
        pass

    def _get_total_exp_consumption(self, members: list[Member],
                                   current_datetime: datetime) -> float:
        """
        Calculate the total expected consumption of all members.

        Args:
            members: List of energy community members
            current_datetime: Current timestamp

        Returns:
            float: Total expected consumption in kW

        Example:
            >>> total = manager._get_total_exp_consumption(members, dt)
        """
        return sum(member.exp_consumption[current_datetime]
                   for member in members)

    def _get_total_sim_consumption(self, members: list[Member],
                                   current_datetime: datetime) -> float:
        """
        Calculate the total simulated consumption of all members.
        """
        return sum(member.sim_consumption[current_datetime]
                   for member in members)

    def _should_recommend(self, current_datetime: datetime) -> bool:
        """
        Check if the manager should recommend an action based
        on the indication interval.

        Args:
            current_datetime: Current timestamp

        Returns:
            bool: True if the manager should recommend an action,
            False otherwise.
        """
        if (current_datetime.hour < self.recommendation_interval[0] or
                current_datetime.hour > self.recommendation_interval[1]):
            return False
        return True


class BasicManager(Manager):
    """
    Basic implementation of an energy system manager.

    This manager implements a simple control strategy based on comparing
    total expected consumption with PV production. It recommends
    decreasing consumption when it exceeds production, and increasing
    consumption otherwise.
    """

    def __init__(self, time_space_handler: TimeSpaceHandler,
                 recommendation_interval: list[int]):
        """
        Initialize a new basic manager.

        Args:
            time_space_handler: Handler for time and space operations
        """
        super().__init__(time_space_handler, recommendation_interval)

    def step(self,
             k: int,
             members: list[Member],
             pv: PVPlant) -> Recommendation:
        """
        Run a single step of the basic manager's control logic.

        If the total expected consumption is greater than the production,
        the manager will recommend a decrease. Otherwise, the manager will
        recommend an increase.

        Args:
            k: Time step index
            members: List of energy community members
            pv: PV plant instance

        Returns:
            Recommendation: Generated recommendation for this time step

        Example:
            >>> recommendation = manager.step(0, members, pv_plant)
        """
        current_datetime = self.time_space_handler.get_datetime_from_k(k)

        if not self._should_recommend(current_datetime):
            new_recommendation = Recommendation(RecommendationType.NONE)
            self.recommendations[current_datetime] = new_recommendation
            return new_recommendation

        total_consumption = self._get_total_exp_consumption(
            members, current_datetime)
        production = pv.power_production_hourly[current_datetime]

        if total_consumption > 1.1 * production:
            new_recommendation = Recommendation(RecommendationType.DECREASE)
            self.recommendations[current_datetime] = new_recommendation
        elif total_consumption < 0.9 * production:
            new_recommendation = Recommendation(RecommendationType.INCREASE)
            self.recommendations[current_datetime] = new_recommendation
        else:
            new_recommendation = Recommendation(RecommendationType.NONE)
            self.recommendations[current_datetime] = new_recommendation

        return new_recommendation


class ReactiveManager(BasicManager):
    """
    Reactive implementation of an energy system manager.

    This manager represents a strong option then the basic manager,
    being able to react to the reaction of the community and
    provide a different recommendation, if the community is not
    reacting as expected.
    """

    def __init__(self, time_space_handler: TimeSpaceHandler,
                 recommendation_interval: list[int]):
        super().__init__(time_space_handler, recommendation_interval)

    def step(self,
             k: int,
             members: list[Member],
             pv: PVPlant) -> Recommendation:
        return super().step(k, members, pv)

    def extra_step(self,
                   k: int,
                   members: list[Member],
                   pv: PVPlant) -> Recommendation | None:
        current_datetime = self.time_space_handler.get_datetime_from_k(k)
        total_sim_consumption = self._get_total_sim_consumption(
            members, current_datetime)
        production = pv.power_production_hourly[current_datetime]

        initial_recommendation = self.recommendations[current_datetime]

        if (
            initial_recommendation.type == RecommendationType.DECREASE and
            total_sim_consumption > 1.1 * production
        ):
            new_recommendation = Recommendation(
                RecommendationType.STRONG_DECREASE)
            self.recommendations[current_datetime] = new_recommendation
        elif (
            initial_recommendation.type == RecommendationType.INCREASE and
            total_sim_consumption < 0.9 * production
        ):
            new_recommendation = Recommendation(
                RecommendationType.STRONG_INCREASE)
            self.recommendations[current_datetime] = new_recommendation
        else:
            new_recommendation = None
        return new_recommendation


class AdaptiveManager(Manager):
    """
    Adaptive implementation of an energy system manager.
    The adaptive manager takes into account the previous
    impact of recommendations in terms of consumption.
    """

    # Class-level constants for recommendation types
    DECREASE_TYPES = [RecommendationType.DECREASE,
                      RecommendationType.STRONG_DECREASE]
    INCREASE_TYPES = [RecommendationType.INCREASE,
                      RecommendationType.STRONG_INCREASE]

    def __init__(self, time_space_handler: TimeSpaceHandler,
                 recommendation_interval: list[int]):
        super().__init__(time_space_handler, recommendation_interval)
        self._impact_cache: dict[int, dict[RecommendationType, float]] = {}
        self._running_sums: dict[RecommendationType, float] = {
            rec_type: 0.0 for rec_type in RecommendationType
        }
        self._running_counts: dict[RecommendationType, int] = {
            rec_type: 0 for rec_type in RecommendationType
        }
        self._last_calculated_k = -1

    def _update_running_stats(self,
                              members: list[Member],
                              k: int) -> None:
        """
        Update running statistics for impact calculations.
        The stats are the sums of the differences between the expected
        consumption and the simulated consumption and the number of times
        the recommendation was made.

        Args:
            members: List of energy community members
            k: Current time step index
        """
        if k <= self._last_calculated_k:
            return

        # Get new data points
        new_date_times = self.time_space_handler.range_hourly[
            self._last_calculated_k + 1:k + 1
        ]

        for date_time in new_date_times:
            if date_time not in self.recommendations:
                continue

            recommendation = self.recommendations[date_time]
            exp_consumption = self._get_total_exp_consumption(
                members, date_time)
            sim_consumption = self._get_total_sim_consumption(
                members, date_time)
            impact = exp_consumption - sim_consumption

            self._running_sums[recommendation.type] += impact
            self._running_counts[recommendation.type] += 1

        self._last_calculated_k = k

    def _get_recommendation_impact(self,
                                   members: list[Member],
                                   target_recommendation: RecommendationType,
                                   k: int) -> float:
        """
        Get the impact for a specific recommendation type, using cached values
        when available.

        Args:
            members: List of energy community members
            target_recommendation: The recommendation type to analyze
            k: Current time step index

        Returns:
            float: Average impact of the recommendation type
        """
        if k not in self._impact_cache:
            self._update_running_stats(members, k)
            self._impact_cache[k] = {
                rec_type: (self._running_sums[rec_type] /
                           self._running_counts[rec_type]
                           if self._running_counts[rec_type] > 0 else 0.0)
                for rec_type in RecommendationType
            }

        return self._impact_cache[k][target_recommendation]

    def _calculate_needed_contribution(self,
                                       members: list[Member],
                                       pv: PVPlant,
                                       current_datetime: datetime) -> float:
        """
        Calculate the needed contribution based on current consumption and
        production.

        Args:
            members: List of energy community members
            pv: PV plant instance
            current_datetime: Current timestamp

        Returns:
            float: The needed contribution
        """
        current_production = pv.power_production_hourly[current_datetime]
        current_consumption = self._get_total_exp_consumption(
            members, current_datetime)
        return current_consumption - current_production

    def _get_relevant_recommendation_types(self,
                                           needed_contribution: float
                                           ) -> list[RecommendationType]:
        """
        Get the relevant recommendation types based on needed contribution.

        Args:
            needed_contribution: The needed contribution

        Returns:
            list[RecommendationType]: List of relevant recommendation types
        """
        if abs(needed_contribution) < 0.1:
            return [RecommendationType.NONE]
        return (self.DECREASE_TYPES if needed_contribution > 0
                else self.INCREASE_TYPES)

    def _find_best_recommendation(
        self,
        needed_contribution: float,
        previous_impact: dict[RecommendationType, float]
    ) -> RecommendationType:
        """
        Find the best recommendation type based on needed contribution and
        previous impacts.

        Args:
            needed_contribution: The needed contribution
            previous_impact: Dictionary mapping recommendation types to their
            historical impacts

        Returns:
            RecommendationType: The best recommendation type
        """
        # Early return for small contributions
        if abs(needed_contribution) < 0.1:
            return RecommendationType.NONE

        recommendations = (self.DECREASE_TYPES if needed_contribution > 0
                           else self.INCREASE_TYPES)

        # Find recommendation with minimum error
        return min(
            recommendations,
            key=lambda r: abs(previous_impact[r] - needed_contribution)
        )

    def step(self,
             k: int,
             members: list[Member],
             pv: PVPlant) -> Recommendation:
        """
        Run a single step of the adaptive manager's control logic.

        Args:
            k: Time step index
            members: List of energy community members
            pv: PV plant instance

        Returns:
            Recommendation: Generated recommendation for this time step
        """
        current_datetime = self.time_space_handler.get_datetime_from_k(k)

        if not self._should_recommend(current_datetime):
            return self._create_none_recommendation(current_datetime)

        needed_contribution = self._calculate_needed_contribution(
            members, pv, current_datetime)

        # Only calculate impacts for relevant recommendation types
        relevant_types = self._get_relevant_recommendation_types(
            needed_contribution)
        previous_impact = {
            rec_type: self._get_recommendation_impact(members, rec_type, k)
            for rec_type in relevant_types
        }

        best_recommendation = self._find_best_recommendation(
            needed_contribution, previous_impact)

        new_recommendation = Recommendation(best_recommendation)
        self.recommendations[current_datetime] = new_recommendation
        return new_recommendation

    def _create_none_recommendation(
        self,
        current_datetime: datetime
    ) -> Recommendation:
        """
        Create and store a NONE recommendation.

        Args:
            current_datetime: Current timestamp

        Returns:
            Recommendation: A NONE recommendation
        """
        new_recommendation = Recommendation(RecommendationType.NONE)
        self.recommendations[current_datetime] = new_recommendation
        return new_recommendation
