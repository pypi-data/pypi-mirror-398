from __future__ import annotations
import datetime
import random
from ..core.solar import PVplant
from .irise import IRISE, House
from .simulator import SynchronizedMember, Manager, COLOR


class CommunityMember(SynchronizedMember):

    def __init__(self, member: House, datetimes: list[datetime.datetime], group_name: str, randomize_ratio: float = .2, averager_depth_in_hours: int = 3):
        super().__init__(member, datetimes, group_name, randomize_ratio, averager_depth_in_hours)

    def day_interactions(self, the_date: datetime.date, day_hour_indices: list[int], interaction: int, init: bool):
        pass

    def hour_interactions(self, the_datetime: datetime.datetime, hour_index: int,  interaction: int, init: bool):
        pass


class DynamicCommunityManager(Manager):
    
    def __init__(self, pv_system: PVplant, no_alert_threshold, randomize_ratio: int = .2, averager_depth_in_hours: int = 3) -> None:
        super().__init__(pv_system, 1, 1, no_alert_threshold=no_alert_threshold, randomize_ratio=randomize_ratio, averager_depth_in_hours=averager_depth_in_hours)
        
        for member in IRISE(pv_system.datetimes, zipcode_pattern='381%').get_houses():
            community_member = CommunityMember(member, self.datetimes, 'ecom')
            self.register_synchronized_member(community_member)
            
        self.color_adapter = None
        self.colors = (COLOR.BLINKING_RED, COLOR.SUPER_RED, COLOR.RED, COLOR.WHITE, COLOR.GREEN, COLOR.SUPER_GREEN, COLOR.BLINKING_GREEN)
        self.color_ratios = (.01, .04, .2, .5, .2, .04, .01)
        
    def day_interactions(self, the_date: datetime.date, day_hour_indices: list[int],   interaction: int, init: bool) -> None:
        if day_hour_indices[0] >= 24 * 7:
            productions_kWh: float = self.actual_productions_kWh[0:day_hour_indices[0]]
            consumptions_kWh: float = self.get_actual_consumptions_kWh('ecom')[0:day_hour_indices[0]]
            self.color_adapter = ColorAdapter(self.colors, self.color_ratios, productions_kWh, consumptions_kWh)

    def hour_interactions(self, the_datetime: datetime.datetime, hour_index: int,  interaction: int, init: bool) -> None:
        production = self.predicted_productions_kWh[hour_index]
        consumption = self.get_predicted_consumption_kWh(hour_index, 'ecom')

        hour_color: COLOR = self.get_hour_colors(hour_index)
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
            if self.color_adapter is not None:
                if abs(consumption - production) > self.no_alert_threshold:
                    hour_color = self.color_adapter.get_color(production, consumption)
        self.set_hour_colors(hour_index, hour_color)

    def finalize(self) -> None:
        pass


class ColorAdapter:

    def __init__(self, colors: tuple[COLOR], color_ratios: tuple[float], supplied_powers: list[float], consumed_powers: list[float]):
        delta_powers = [supplied_powers[i] - consumed_powers[i] for i in range(len(consumed_powers))]
        delta_powers.extend([-d for d in delta_powers[::-1]])
        delta_powers.sort()
        number_of_delta_powers_per_color: list[int] = [int(color_ratio * len(delta_powers)) for color_ratio in color_ratios]
        number_of_delta_powers_per_color[int((2 * len(colors) - 1) / 2)] += len(delta_powers) - sum(number_of_delta_powers_per_color)  # add missing values, due to rounding, to central color
        self.colors: list[COLOR] = colors
        self.color_index_deltas_powers = {i:[] for i in range(len(colors))}
        color_index = 0
        self.color_index_deltas_powers[0] = list()
        for i in range(len(delta_powers)):
            if len(self.color_index_deltas_powers[color_index]) < number_of_delta_powers_per_color[color_index]:
                self.color_index_deltas_powers[color_index].append(delta_powers[i])
            else:
                color_index += 1
                self.color_index_deltas_powers[color_index].append(delta_powers[i])

    def get_color(self, supplied_power, consumed_power) -> COLOR:
        delta_power = supplied_power - consumed_power
        returned_color = COLOR.WHITE
        if len(self.color_index_deltas_powers[0])>0 and delta_power < self.color_index_deltas_powers[0][-1]:
            returned_color = self.colors[0]
        elif len(self.color_index_deltas_powers[len(self.colors)-1]) > 0 and delta_power > self.color_index_deltas_powers[len(self.colors)-1][0]:
            returned_color: COLOR = self.colors[-1]
        else:
            for i in range(1, len(self.colors)-1, 1):
                if len(self.color_index_deltas_powers[i]) > 0 and self.color_index_deltas_powers[i][0] <= delta_power <= self.color_index_deltas_powers[i][-1]:
                    returned_color = self.colors[i]
        if returned_color is None:
            return COLOR.WHITE
        else:
            return returned_color
