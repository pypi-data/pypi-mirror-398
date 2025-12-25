import os
from batem.core.library import Setup



class WeatherFilePathBuilder:

    def __init__(self):
        pass

    def get_weather_json_file_path(self, location: str) -> str:
        """
        Get the path to the weather json file for a given location.

        Args:
            location: The location to get the weather json file path for.

        Returns:
            The path to the weather json file for the given location.
        """

        data_folder = Setup.folder_path('data')
        path = data_folder / f"{location}.json"

        return str(path)
