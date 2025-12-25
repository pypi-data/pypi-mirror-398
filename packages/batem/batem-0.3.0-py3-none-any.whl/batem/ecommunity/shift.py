from __future__ import annotations
import datetime
import random
from ..core.solar import PVplant, PVplantProperties, MOUNT_TYPE, SolarModel
from ..core.weather import SiteWeatherData, SWDbuilder
from .irise import IRISE, House
from .simulator import SynchronizedMember, Manager, COLOR


class ShiftCommunityMember(SynchronizedMember):

    def __init__(self, member: House, datetimes: list[datetime.datetime], group_name: str, randomize_ratio: float = .2, averager_depth_in_hours: int = 3):
        super().__init__(member, datetimes, group_name,
                         randomize_ratio, averager_depth_in_hours)

    def day_interactions(self, the_date: datetime.date, day_hour_indices: list[int], interaction: int, init: bool):
        power_to_shift = 0
        green_indices = list()
        for hour_index in day_hour_indices:
            if self.manager.get_hour_colors(hour_index) == COLOR.RED:
                self._actual_consumptions_kWh[hour_index] = self._predicted_consumptions_kWh[hour_index] * (
                    self.presences[hour_index] * random.uniform(0.5, 1) + (1 - self.presences[hour_index]))
                power_to_shift += self._predicted_consumptions_kWh[hour_index] - \
                    self._actual_consumptions_kWh[-1]
            else:
                self._actual_consumptions_kWh[hour_index] = self._predicted_consumptions_kWh[hour_index] * (
                    self.presences[hour_index] * random.uniform(.8, 1.2) + (1 - self.presences[hour_index]))
            if self.manager.get_hour_colors(hour_index) == COLOR.GREEN:
                green_indices.append(hour_index)
        if self.presences[hour_index] and len(green_indices) > 0:
            repartition: list[float] = [random.uniform(
                0, 1) for i in range(len(green_indices))]
            sum_repartition: float = sum(repartition)
            for i in range(len(green_indices)):
                self._actual_consumptions_kWh[green_indices[i]
                                              ] += power_to_shift * repartition[i] / sum_repartition

    def hour_interactions(self, the_datetime: datetime.datetime, hour_index: int,  interaction: int, init: bool):
        pass


class CommunityManager(Manager):

    def __init__(self, pv_system: PVplant, no_alert_threshold, randomize_ratio: int = .2, averager_depth_in_hours: int = 3) -> None:
        super().__init__(pv_system, 1, 1, no_alert_threshold=no_alert_threshold,
                         randomize_ratio=randomize_ratio, averager_depth_in_hours=averager_depth_in_hours)

        for member in IRISE(pv_system.datetimes, zipcode_pattern='381%').get_houses():
            member_agent = ShiftCommunityMember(member, self.datetimes, 'ecom')
            self.register_synchronized_member(member_agent)

    def hour_interactions(self, the_datetime: datetime.datetime, hour_index: int,  interaction: int, init: bool) -> None:
        production: float = self.predicted_productions_kWh[hour_index]
        consumption: float = self.get_predicted_consumption_kWh(hour_index)
        hour_color = COLOR.WHITE
        if self.datetimes[hour_index].hour > 7 and self.datetimes[hour_index].hour < 23:
            if production > consumption + self.no_alert_threshold:
                hour_color = COLOR.GREEN
            elif consumption > production + self.no_alert_threshold:
                hour_color = COLOR.RED
        self.set_color(hour_index, hour_color)

    def day_interactions(self, the_date: datetime.date, day_hour_indices: list[int], interaction: int, init: bool) -> None:
        day_productions_kWh = [self.predicted_productions_kWh[k]
                               for k in day_hour_indices]
        day_consumptions = [0 for i in range(len(day_productions_kWh))]
        for member in self.synchronized_member_groups['ecom']:
            for i in range(len(day_hour_indices)):
                day_consumptions[i] += member._predicted_consumptions_kWh[day_hour_indices[i]]
        for i in range(len(day_productions_kWh)):
            if self.datetimes[i].hour < 8 or self.datetimes[i].hour > 22:
                self.set_hour_colors(day_hour_indices[i], COLOR.WHITE)
            elif day_productions_kWh[i] > day_consumptions[i] + self.no_alert_threshold:
                self.set_hour_colors(day_hour_indices[i], COLOR.GREEN)
            elif day_consumptions[i] > day_productions_kWh[i] + self.no_alert_threshold:
                self.set_hour_colors(day_hour_indices[i], COLOR.RED)
            else:
                self.set_hour_colors(day_hour_indices[i], COLOR.WHITE)

    def finalize(self) -> None:
        pass


if __name__ == '__main__':
    site_weather_data: SiteWeatherData = SWDbuilder('grenoble1979-2022.json', from_requested_stringdate='1/01/2021',
                                                                to_requested_stringdate='1/01/2022', altitude=330, albedo=0.1, pollution=0.1, location="Grenoble").site_weather_data

    pv_plant_properties = PVplantProperties()
    pv_plant_properties.skyline_azimuths_altitudes_in_deg: list[tuple[float, float]] = ([(-180.0, 13.8), (-170.0, 18.9), (-145.1, 9.8), (-120.0, 18.3), (-96.1, 17.3), (-60.8, 6.2), (
        -14.0, 2.6), (-8.4, 5.6), (0.8, 2.6), (21.6, 5.5), (38.1, 14.6), (49.4, 8.9), (60.1, 11.3), (87.4, 10.4), (99.3, 12.0), (142.1, 2.6), (157.8, 4.0), (175.1, 17.1), (180.0, 15.9)])
    pv_plant_properties.surfacePV_in_m2: float = 16
    pv_plant_properties.panel_height_in_m: float = 1.2
    pv_plant_properties.efficiency = 0.2 * 0.95
    pv_plant_properties.temperature_coefficient: float = 0.0035
    pv_plant_properties.array_width: float = 4  # in m
    pv_plant_properties.exposure_in_deg = 0  # TO BE ADJUSTED IF NEEDED
    pv_plant_properties.slope_in_deg = 0  # TO BE ADJUSTED IF NEEDED
    pv_plant_properties.distance_between_arrays_in_m = 1.2  # TO BE ADJUSTED IF NEEDED
    # TO BE ADJUSTED IF NEEDED
    pv_plant_properties.mount_type: MOUNT_TYPE = MOUNT_TYPE.FLAT

    pv_plant: PVplant = PVplant(SolarModel(
        site_weather_data), pv_plant_properties)

    manager = CommunityManager(pv_plant, no_alert_threshold=2)
    manager.run()
