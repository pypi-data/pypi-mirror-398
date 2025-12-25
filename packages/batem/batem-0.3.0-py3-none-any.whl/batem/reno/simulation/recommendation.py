"""
Recommendation system for energy optimization.

This module provides classes for generating and managing energy-related
recommendations, particularly for optimizing PV system configurations
and energy consumption patterns.
"""

from enum import Enum


class RecommendationType(Enum):
    """
    Types of energy-related recommendations.

    This enum defines the possible types of recommendations that can be
    generated for energy optimization:
    - NONE: No recommendation needed
    - INCREASE: Recommendation to increase a parameter
    - DECREASE: Recommendation to decrease a parameter
    """

    NONE = "none"
    INCREASE = "increase"
    DECREASE = "decrease"
    STRONG_DECREASE = "strong_decrease"
    STRONG_INCREASE = "strong_increase"


class Recommendation:
    """
    Represents an energy optimization recommendation.

    This class encapsulates a single recommendation for energy optimization,
    including its type and any associated parameters or values.

    Attributes:
        type: Type of recommendation (from RecommendationType enum)
    """

    def __init__(self, type: RecommendationType):
        """
        Initialize a new recommendation.

        Args:
            type: Type of recommendation to create

        Example:
            >>> rec = Recommendation(RecommendationType.INCREASE)
        """
        self.type = type
