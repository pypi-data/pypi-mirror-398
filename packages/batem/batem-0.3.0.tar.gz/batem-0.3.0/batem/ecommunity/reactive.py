from __future__ import annotations
import datetime
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


class ReactiveCommunityManager(Manager):
    
    def __init__(self, pv_system: PVplant, no_alert_threshold, randomize_ratio: int = .2, averager_depth_in_hours: int = 3) -> None:
        super().__init__(pv_system, 0, 2, no_alert_threshold=no_alert_threshold, randomize_ratio=randomize_ratio, averager_depth_in_hours=averager_depth_in_hours)
        
        for member in IRISE(pv_system.datetimes, zipcode_pattern='381%').get_houses():
            community_member = CommunityMember(member, self.datetimes, 'ecom')
            self.register_synchronized_member(community_member)
        
        # self.candidate_hour_color: ecommunity.simulator.COLOR = None
    
    def day_interactions(self, the_date: datetime.date, day_hour_indices: list[int],   interaction: int, init: bool) -> None:
        pass 

    def hour_interactions(self, the_datetime: datetime.datetime, hour_index: int,  interaction: int, init: bool) -> None:
        if interaction == 1:  # determination of the color
            production_kWh: float = self.predicted_productions_kWh[hour_index]
            consumption_kWh: float = sum([member._predicted_consumptions_kWh[hour_index] for member in self.members])
            hour_color: COLOR = self.get_hour_colors(hour_index)
            if 7 < self.datetimes[hour_index].hour < 23:
                if production_kWh > consumption_kWh + self.no_alert_threshold:
                    hour_color = COLOR.GREEN
                elif consumption_kWh > production_kWh + self.no_alert_threshold:
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
