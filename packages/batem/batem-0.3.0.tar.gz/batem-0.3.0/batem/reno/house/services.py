import csv
from batem.reno.constants import APPLIANCES
from batem.reno.house.model import House, Appliance, TimeRange
import pandas as pd
from datetime import datetime

from batem.reno.utils import TimeSpaceHandler


class ApplianceInferrer:
    def __init__(self):
        pass

    def determine_appliance_type(self, name: str) -> APPLIANCES:
        """
        Infer the type of an appliance from the name.
        """
        inferred_type: APPLIANCES | None = None
        for appliance_type in APPLIANCES:
            if appliance_type.name.lower() in name.lower():
                inferred_type = appliance_type
                break
        if inferred_type is None:
            inferred_type = APPLIANCES.OTHER
        return inferred_type


class ConsumptionAggregatorAppliance:
    def __init__(self, appliance: Appliance):
        self.appliance = appliance

    def get_consumption_hourly(self) -> dict[datetime, float]:
        """
        Convert 10-minute consumption data to hourly intervals.

        Uses floor('h') instead of resample('h') to prevent creating
        extra timestamps during DST transitions.

        Returns:
            dict[datetime, float]: Dictionary of hourly consumption data
        """
        consumption_series = pd.Series(self.appliance.consumption.usage_10min)
        hourly_consumption = consumption_series.groupby(
            consumption_series.index.floor('h')  # type: ignore
        ).sum()
        return hourly_consumption.to_dict()


class ConsumptionTrimmer:
    def __init__(self, house: House):
        self.house = house

    def trim_consumption_house(self, time_space_handler: TimeSpaceHandler):
        self.house.time_range = TimeRange(
            start_time=time_space_handler.start_time,
            end_time=time_space_handler.end_time
        )
        for appliance in self.house.appliances:
            self.trim_consumption_appliance(appliance, time_space_handler)

    def trim_consumption_appliance(self, appliance: Appliance,
                                   time_space_handler: TimeSpaceHandler):
        """
        Trim consumption data to the specified time range.

        Args:
            time_space_handler: TimeSpaceHandler instance defining the
                time range to trim to
        """
        new_range = TimeRange(
            start_time=time_space_handler.start_time,
            end_time=time_space_handler.end_time
        )

        appliance.consumption.usage_10min = {
            k: v for k, v in appliance.consumption.usage_10min.items()
            if new_range.contains(k)}


class ConsumptionAggregator:
    def __init__(self, house: House):
        self.house = house

    def get_total_consumption_hourly(self) -> dict[datetime, float]:
        """
        Aggregates consumption from all appliances at hourly intervals.

        Returns a dictionary with the total consumption for each hour.
        """
        # Get 10-minute consumption
        total_consumption_10min = self.get_total_consumption_10min()

        # Get hourly consumption by properly grouping 10-minute data
        # This properly aggregates all 10-minute readings within each hour
        # We do this because resmapling adds the timestamp for DST transitions
        consumption_series = pd.Series(total_consumption_10min)
        hourly_consumption = consumption_series.groupby(
            consumption_series.index.floor('h')  # type: ignore
        ).sum()

        return hourly_consumption.to_dict()

    def get_total_consumption_10min(self) -> dict[datetime, float]:
        """
        Aggregates consumption from all appliances at 10-minute intervals.

        Returns a dictionary with the total
        consumption for each 10-minute interval.
        """

        appliances_consumption_10min = [
            appliance.consumption.usage_10min
            for appliance in self.house.appliances
        ]

        # Get all unique timestamps
        all_timestamps = set()
        for consumption_in_time in appliances_consumption_10min:
            all_timestamps.update(consumption_in_time.keys())

        # Sum consumption for each timestamp
        return {
            timestamp: sum(
                consumption_in_time.get(timestamp, 0.0)
                for consumption_in_time in appliances_consumption_10min
            )
            for timestamp in sorted(all_timestamps)
        }


class ConsumptionExporter:
    def __init__(self, house: House):
        self.house = house

    def get_house_consumption(self, hourly: bool = False
                              ) -> dict[datetime, float]:
        aggregator = ConsumptionAggregator(self.house)
        if hourly:
            return aggregator.get_total_consumption_hourly()
        else:
            return aggregator.get_total_consumption_10min()

    def get_appliances_consumption(self, appliances: list[Appliance],
                                   hourly: bool = False
                                   ) -> dict[str, dict[datetime, float]]:
        consumption_by_appliance = {}

        for appliance in appliances:
            aggregator = ConsumptionAggregatorAppliance(appliance)
            if hourly:
                consumption_by_appliance[appliance.name] = \
                    aggregator.get_consumption_hourly()
            else:
                consumption_by_appliance[appliance.name] = \
                    appliance.consumption.usage_10min
        return consumption_by_appliance

    def to_csv(self, path: str, hourly: bool = False):
        """
        Save the house consumption data to a CSV file.

        The CSV file will have the following format:
        - Header: timestamp,total,appliance_1,appliance_2,...
        - Timestamp format: YYYY-MM-DD HH:MM:SS
        - Consumption values in kW

        Args:
            path: Path to save the CSV file
            hourly: Whether to use hourly data (default: False)

        Example:
            >>> house.to_csv("house_1_consumption.csv", hourly=True)
        """
        consumption_by_time = self.get_house_consumption(hourly)
        consumption_by_appliance = self.get_appliances_consumption(
            self.house.appliances, hourly)

        with open(path, "w") as f:
            writer = csv.writer(f)

            self._write_header(writer)

            # Write the first part with the aggregated consumption
            for timestamp, consumption in consumption_by_time.items():
                result = {'timestamp': timestamp, 'total': consumption}

                # Iterate over all appliances and add their consumption
                # to the row
                for appliance in self.house.appliances:
                    result[appliance.name] = \
                        consumption_by_appliance[appliance.name][timestamp]

                writer.writerow(result.values())

        print(f"House {self.house.house_id} saved to csv.")

    def _write_header(self, writer: csv.writer):  # type: ignore
        header = ["timestamp", "total"]
        for appliance in self.house.appliances:
            key = f'{appliance.appliance_id}_{appliance.name}_{appliance.type.value}'
            header.append(key)
        writer.writerow(header)

    def get_appliance_consumption(
            self, appliance: Appliance,
            timestamp: datetime,
            hourly: bool = False) -> float:
        """
        Get the consumption for an appliance at a given timestamp.
        """
        if hourly:
            hourly_consumption = ConsumptionAggregatorAppliance(
                appliance).get_consumption_hourly()
            if timestamp in hourly_consumption:
                appliance_consumption = \
                    hourly_consumption[timestamp]
            else:
                appliance_consumption = 0.0
        else:
            if timestamp in appliance.consumption.usage_10min:
                appliance_consumption = \
                    appliance.consumption.usage_10min[timestamp]
            else:
                appliance_consumption = 0.0
        return appliance_consumption
