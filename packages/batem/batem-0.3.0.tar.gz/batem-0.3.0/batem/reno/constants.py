"""
Constants and enumerations used throughout the reno package.

This module defines various constants and enumerations used for:
- Appliance types and categories
- Time and date formats
- Timezone configurations
"""

from enum import Enum


class APPLIANCES(Enum):
    """
    Enumeration of supported household appliances.

    This enumeration defines the types of appliances that can be modeled
    in the energy consumption calculations.

    Attributes:
        TV: Television
        AIR_CONDITIONER: Air conditioning unit
        DISH_WASHER: Dishwashing machine
        ELECTRIC_OVEN: Electric oven
        MICROWAVE: Microwave oven
        WASHING_MACHINE: Washing machine
        CLOTHES_DRYER: Clothes dryer
        FRIDGE: Refrigerator
        OTHER: Other electrical appliances
    """
    TV = "TV"
    AIR_CONDITIONER = "Air Conditioner"
    DISH_WASHER = "Dish Washer"
    ELECTRIC_OVEN = "Electric Oven"
    MICROWAVE = "Microwave"
    WASHING_MACHINE = "Washing Machine"
    CLOTHES_DRYER = "Clothes Dryer"
    FRIDGE = "Fridge"
    LIGHT_CONSUMPTION = "Total site light consumption ()"
    OTHER = "Other"


# Time and date format strings
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"  # Format: 2023-01-01 12:00:00
DATE_FORMAT = "%Y-%m-%d"  # Format: 2023-01-01

# Timezone names for supported locations
TZ_FRANCE_NAME = 'Europe/Paris'  # Timezone for France
TZ_ROMANIA_NAME = 'Europe/Bucharest'  # Timezone for Romania


class MANAGER_TYPE(Enum):
    BASIC = "basic"
    REACTIVE = "reactive"
    ADAPTIVE = "adaptive"
