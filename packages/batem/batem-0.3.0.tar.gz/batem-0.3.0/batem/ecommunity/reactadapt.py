from __future__ import annotations
import datetime
import random
from ..core.solar import PVplant
from .irise import IRISE, House
from .simulator import SynchronizedMember, Manager, COLOR
from .indicators import color_statistics


class CommunityMember(SynchronizedMember):

    def __init__(self, member: House, datetimes: list[datetime.datetime], group_name: str, randomize_ratio: float = .2, averager_depth_in_hours: int = 3):
        super().__init__(member, datetimes, group_name, randomize_ratio, averager_depth_in_hours)

    def day_interactions(self, the_date: datetime.date, day_hour_indices: list[int], interaction: int, init: bool):
        pass

    def hour_interactions(self, the_datetime: datetime.datetime, hour_index: int,  interaction: int, init: bool):
        pass


class ReactiveAdaptiveCommunityManager(Manager):

    def __init__(self, pv_system: PVplant, no_alert_threshold, randomize_ratio: int = .2, averager_depth_in_hours: int = 3) -> None:
        super().__init__(pv_system, 1, 2, no_alert_threshold=no_alert_threshold, randomize_ratio=randomize_ratio, averager_depth_in_hours=averager_depth_in_hours)

        for member in IRISE(pv_system.datetimes, zipcode_pattern='381%').get_houses():
            member_agent = CommunityMember(member, self.datetimes, 'ecom')
            self.register_synchronized_member(member_agent)

        self.color_delta_power_dict = None
        self.predicted_consumptions_kWh = self.get_predicted_consumptions_kWh('ecom')

    def day_interactions(self, the_date: datetime.date, day_hour_indices: list[int], interaction: int, init: bool) -> None:
        if day_hour_indices[0] >= 24 * 7:
            predicted_consumptions: list[float] = [sum([member._predicted_consumptions_kWh[i] for member in self.members]) for i in range(0, day_hour_indices[0])]
            actual_consumptions: list[float] = [sum([member._actual_consumptions_kWh[i] for member in self.members]) for i in range(0, day_hour_indices[0])]
            colors: list[COLOR] = [self.get_hour_colors(i) for i in range(0, day_hour_indices[0])]
            # compute the average consumption variations of the distribution per color
            _, color_level_average_values = color_statistics(actual_consumptions, predicted_consumptions, colors)
            self.color_delta_power_dict = {color: color_level_average_values[color] for color in color_level_average_values}

    def hour_interactions(self, the_datetime: datetime.datetime, hour_index: int,  interaction: int, init: bool) -> None:
        productions_kWh: float = self.predicted_productions_kWh[hour_index]
        consumptions_kWh: float = self.predicted_consumptions_kWh[hour_index]

        hour_color: COLOR = self.get_hour_colors(hour_index)
        if interaction == 1:
            if hour_index < 24 * 7 or random.uniform(0, 1) <= .05:
                productions_kWh: float = self.predicted_productions_kWh[hour_index]
                consumptions_kWh: float = self.get_predicted_consumption_kWh(hour_index)
                hour_color = COLOR.WHITE
                if self.datetimes[hour_index].hour > 7 and self.datetimes[hour_index].hour < 23:
                    if productions_kWh > consumptions_kWh + self.no_alert_threshold:
                        hour_color = COLOR.GREEN
                    elif consumptions_kWh > productions_kWh + self.no_alert_threshold:
                        hour_color = COLOR.RED
            else:
                if self.color_delta_power_dict is not None:
                    color_match = None
                    for color in self.color_delta_power_dict:  # search for the color that best match the need in term of historical consumption variations
                        match = abs(consumptions_kWh - productions_kWh + self.color_delta_power_dict[color])
                        if color_match is None or match < color_match[1]:
                            color_match = (color, match)
                    if match > self.no_alert_threshold:
                        hour_color = color_match[0]
                else: # if less than one week of history, apply reactive strategy
                    if productions_kWh > consumptions_kWh + self.no_alert_threshold:
                        hour_color = COLOR.GREEN
                    elif consumptions_kWh > productions_kWh + self.no_alert_threshold:
                        hour_color = COLOR.RED
            self.set_hour_colors(hour_index, hour_color)
        elif interaction == 0:
            hour_color = self.get_hour_colors(hour_index)
            if hour_color != COLOR.WHITE:
                production_kWh: float = self.actual_productions_kWh[hour_index]
                consumption_kWh: float = sum([member._actual_consumptions_kWh[hour_index] for member in self.members])
                if hour_color == COLOR.RED and (production_kWh + self.no_alert_threshold < consumption_kWh):
                    self.set_hour_colors(hour_index, COLOR.SUPER_RED)
                elif hour_color == COLOR.GREEN and (consumption_kWh + self.no_alert_threshold < production_kWh):
                    self.set_hour_colors(hour_index, COLOR.SUPER_GREEN)
                else:
                    self.set_hour_colors(hour_index, hour_color)

    def finalize(self) -> None:
        pass
