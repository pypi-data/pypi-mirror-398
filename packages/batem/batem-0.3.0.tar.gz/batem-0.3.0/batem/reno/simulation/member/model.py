"""
Member model for energy community simulation.

This module provides the Member class that represents a participant in
the energy community, managing their consumption patterns and responses
to energy management recommendations.
"""

from datetime import datetime
import random
from batem.reno.house.model import House
from batem.reno.simulation.recommendation import (
    Recommendation, RecommendationType)

from batem.reno.utils import TimeSpaceHandler
import numpy


class Member:
    """
    Represents a member of the energy community.

    This class models a community member's energy consumption behavior,
    including their expected consumption and how they respond to energy
    management recommendations.

    Attributes:
        house: House instance associated with the member
        time_space_handler: Handler for time and space operations
        exp_consumption: Dictionary of expected hourly consumption values
        sim_consumption: Dictionary of simulated hourly consumption values
    """

    def __init__(self, time_space_handler: TimeSpaceHandler, house: House):
        """
        Initialize a new community member.

        Args:
            time_space_handler: Handler for time and space operations
            house: House instance associated with the member

        Example:
            >>> member = Member(time_space_handler, house)
        """

        self.house = house
        self.time_space_handler = time_space_handler
        self.presence: dict[datetime, bool] = {}
        self.init_consumption()

    def init_consumption(self):
        """
        Initialize the expected and simulated consumption data.

        The expected consumption is copied from the house's hourly
        consumption data, while the simulated consumption is initialized
        to zero for all timestamps.
        """
        self.exp_consumption = self.house.total_consumption_hourly.copy()
        self.sim_consumption = {date: 0.0 for date in self.exp_consumption}

    def step(self, k: int, recommendation: Recommendation) -> None:
        """
        Execute a single simulation step for the member.

        The member's simulated consumption is adjusted based on the
        manager's recommendation:
        - DECREASE: Reduce consumption by random factor between 0.75 and 1.0
        - INCREASE: Increase consumption by random factor between 1.0 and 1.5
        - NONE: Keep consumption unchanged

        Args:
            k: Current simulation step index
            recommendation: Energy management recommendation

        Example:
            >>> member.step(0, Recommendation(RecommendationType.DECREASE))
        """
        current_datetime = self.time_space_handler.get_datetime_from_k(k)
        base_consumption = self.exp_consumption[current_datetime]

        is_present = self.presence_model(current_datetime)
        self.presence[current_datetime] = is_present

        if is_present:
            if recommendation.type == RecommendationType.DECREASE:
                adjustment = numpy.random.uniform(0.75, 1.0)
            elif recommendation.type == RecommendationType.INCREASE:
                adjustment = numpy.random.uniform(1.0, 1.5)
            else:
                adjustment = 1.0
        else:
            adjustment = 1.0

        self.sim_consumption[current_datetime] = base_consumption * adjustment

    def extra_step(self, k: int, recommendation: Recommendation | None) -> None:
        """
        Execute a single simulation step for the member.
        """

        if recommendation is None:
            return

        current_datetime = self.time_space_handler.get_datetime_from_k(k)
        base_consumption = self.exp_consumption[current_datetime]

        if recommendation.type == RecommendationType.STRONG_DECREASE:
            adjustment = numpy.random.uniform(0.5, 0.75)
        elif recommendation.type == RecommendationType.STRONG_INCREASE:
            adjustment = numpy.random.uniform(1.5, 2.0)
        else:
            adjustment = 1.0

        self.sim_consumption[current_datetime] = base_consumption * adjustment

    def presence_model(self, current_datetime: datetime) -> bool:
        """
        This function models the presence of the member
        in the energy community.
        It is based on the following rules:
        - If the hour is before 8 or after 22, the member is not present
        - If the weekday is between 0 and 5,
        the member is present with a probability of 0.35
        - If the weekday is between 6 and 7,
        the member is present with a probability of 0.95
        - If the weekday is between 8 and 18,
        the member is present with a probability of 0.70
        - If the weekday is between 19 and 21,
        the member is present with a probability of 0.80
        - If the weekday is between 22 and 23,
        the member is present with a probability of 0.95
        - If the weekday is between 24 and 25,
        the member is present with a probability of 0.35
        """
        if current_datetime.hour < 8 or current_datetime.hour > 22:
            return False
        if current_datetime.weekday() <= 5:
            if 8 <= current_datetime.hour <= 18:
                return random.uniform(0, 1) < .35
            else:
                return random.uniform(0, 1) < .95
        else:
            if 8 <= current_datetime.hour <= 18:
                return random.uniform(0, 1) < .70
            else:
                return random.uniform(0, 1) < .80
