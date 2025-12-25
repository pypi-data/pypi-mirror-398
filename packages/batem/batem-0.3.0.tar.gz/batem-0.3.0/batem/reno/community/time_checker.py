

import json
from batem.reno.house.creation import HouseBuilder
from batem.reno.house.model import House
from batem.reno.utils import FilePathBuilder, TimeSpaceHandler, parse_args


class TimeChecker:
    """
    This class is used to check if the houses
    have data for the simulation period.
    It also exports the valid houses to a JSON file.
    """

    def __init__(self, time_space_handler: TimeSpaceHandler):
        self.time_space_handler = time_space_handler

    def get_valid_houses(self, houses: list[House]):
        """Returns the houses that have data for the simulation period."""

        valid_houses = []
        for house in houses:
            if self.check_house_for_matching_start_and_end_time(house):
                valid_houses.append(house)
        return valid_houses

    def get_valid_houses_ids_from_json(self) -> list[int]:
        """Returns the valid houses from a JSON file."""
        path = FilePathBuilder().get_community_valid_houses_path(
            self.time_space_handler)
        with open(path, "r") as f:
            return json.load(f)

    def check_house_for_matching_start_and_end_time(
            self, house: House) -> bool:
        """
        Check if the house has data for the simulation period.
        If yes, returns True.
        If not, prints a warning message and returns False.
        """

        start_time_matches = (house.start_time
                              <= self.time_space_handler.start_time)
        end_time_matches = (house.end_time
                            >= self.time_space_handler.end_time)
        matches = start_time_matches and end_time_matches
        if matches:
            return True
        else:
            if not start_time_matches:
                print(
                    f"House {house.house_id} does not match the time space"
                    f" handler because start time {house.start_time} is after"
                    f" {self.time_space_handler.start_time}")
            elif not end_time_matches:
                print(
                    f"House {house.house_id} does not match the time space"
                    f" handler because end time {house.end_time} is before"
                    f" {self.time_space_handler.end_time}")
            return False

    def export_valid_houses(self, houses: list[House]):
        """Exports the valid houses to a JSON file."""
        valid_houses = self.get_valid_houses(houses)
        path = FilePathBuilder().get_community_valid_houses_path(
            self.time_space_handler)
        house_ids = [house.house_id for house in valid_houses]
        with open(path, "w") as f:
            json.dump(house_ids, f, indent=4)


if __name__ == "__main__":
    # python batem/reno/community/time_checker.py --location Grenoble

    args = parse_args()

    # Iterate and find the best start and end date
    # for the number of valid houses
    months = [1, 2, 3, 4, 5, 6]
    max_valid_houses = 0

    for month in months:
        start_date = f"01/{month}/1998"
        end_date = f"01/{month}/1999"
        time_space_handler = TimeSpaceHandler(
            location=args.location,
            start_date=start_date,
            end_date=end_date)
        houses = HouseBuilder().build_houses_from_db_records(exclude_consumption=True)
        valid_houses = TimeChecker(time_space_handler).get_valid_houses(houses)
        if len(valid_houses) > max_valid_houses:
            max_valid_houses = len(valid_houses)
            best_start_date = start_date
            best_end_date = end_date

    print(f"Found {max_valid_houses} valid houses for {best_start_date} to "
          f"{best_end_date}")

    # Export the valid houses to a JSON file
    time_space_handler = TimeSpaceHandler(
        location=args.location,
        start_date=best_start_date,
        end_date=best_end_date)
    houses = HouseBuilder().build_houses_from_db_records(exclude_consumption=True)
    valid_houses = TimeChecker(time_space_handler).get_valid_houses(houses)
    TimeChecker(time_space_handler).export_valid_houses(valid_houses)
