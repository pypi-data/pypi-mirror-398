from __future__ import annotations
import datetime
from ..core.solar import PVplant
from .irise import IRISE, House
from .simulator import SynchronizedMember, Manager


class CommunityMember(SynchronizedMember):

    def __init__(self, member: House, datetimes: list[datetime.datetime], group_name: str, randomize_ratio: float = .2, averager_depth_in_hours: int = 3):
        super().__init__(member, datetimes, group_name, randomize_ratio, averager_depth_in_hours)

    def day_interactions(self, the_date: datetime.date, day_hour_indices: list[int], interaction: int, init: bool):
        pass

    def hour_interactions(self, the_datetime: datetime.datetime, hour_index: int,  interaction: int, init: bool):
        pass


class NoSignalCommunityManager(Manager):

    def __init__(self, pv_system: PVplant, number_of_day_interactions: int, number_of_hour_interactions: int, no_alert_threshold, randomize_ratio: int = .2, averager_depth_in_hours: int = 3) -> None:
        super().__init__(pv_system, number_of_day_interactions, number_of_hour_interactions, no_alert_threshold=no_alert_threshold, randomize_ratio=randomize_ratio, averager_depth_in_hours=averager_depth_in_hours)

        for house in IRISE(pv_system.datetimes, zipcode_pattern='381%').get_houses():
            member_agent = CommunityMember(house, self.datetimes, 'ecom')
            self.register_synchronized_member(member_agent)

    def day_interactions(self, the_date: datetime.date, day_hour_indices: list[int], interaction: int, init: bool) -> None:
        pass

    def hour_interactions(self, the_datetime: datetime.datetime, hour_index: int,  interaction: int, init: bool) -> None:
        pass

    def finalize(self) -> None:
        pass
