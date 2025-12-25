

from datetime import datetime
from batem.reno.house.model import House
from batem.reno.pv.model import PVPlant
from batem.reno.utils import TimeSpaceHandler


class EnergyCommunity:
    def __init__(self, time_space_handler: TimeSpaceHandler):

        self.time_space_handler: TimeSpaceHandler = time_space_handler

        self.houses: list[House] = []

        self.total_consumption: dict[datetime, float] = {}

        self.pv_plant: PVPlant

    def compute_total_consumption(self):
        """
        Compute the total consumption of the community.
        """
        for house in self.houses:
            for time, consumption in house.total_consumption_hourly.items():
                if time in self.total_consumption:
                    self.total_consumption[time] += consumption
                else:
                    self.total_consumption[time] = consumption
