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


class BasicCommunityManager(Manager):

    def __init__(self, pv_system: PVplant, no_alert_threshold, randomize_ratio: int = .2, averager_depth_in_hours: int = 3) -> None:
        super().__init__(pv_system, 1, 1, no_alert_threshold=no_alert_threshold, randomize_ratio=randomize_ratio, averager_depth_in_hours=averager_depth_in_hours)
        irise = IRISE(pv_system.datetimes, zipcode_pattern='381%')
        for house in irise.get_houses():
            member_agent = CommunityMember(house, self.datetimes, 'ecom')
            self.register_synchronized_member(member_agent)

    def day_interactions(self, the_date: datetime.date, day_hour_indices: list[int], interaction: int, init: bool) -> None:
        pass
        
    def hour_interactions(self, the_datetime: datetime.datetime, hour_index: int,  interaction: int, init: bool) -> None:
        production_kWh: float = self.actual_productions_kWh[hour_index]
        consumption_kWh: float = self.get_predicted_consumption_kWh(hour_index=hour_index)
        hour_color = COLOR.WHITE
        if self.datetimes[hour_index].hour > 7 and self.datetimes[hour_index].hour < 23:
            if production_kWh > consumption_kWh + self.no_alert_threshold:
                hour_color = COLOR.GREEN
            elif consumption_kWh > production_kWh + self.no_alert_threshold:
                hour_color = COLOR.RED
        self.set_hour_colors(hour_index, hour_color)

    def finalize(self) -> None:
        pass
