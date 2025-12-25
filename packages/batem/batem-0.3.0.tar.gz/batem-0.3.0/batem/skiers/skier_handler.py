from typing import Optional
import pandas as pd
from datetime import time as time_lib
import numpy as np

from batem.skiers.skier import CheckInType, SkierData, SkipassInteraction
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

LATE_ARRIVAL_TIME = time_lib(17, 0, 0)
MIN_STAYING_TIME = pd.Timedelta(minutes=30)
MIN_TIME_BETWEEN_SKILIFTS = pd.Timedelta(minutes=2)


class SkierDayDataHandler:

    def __init__(self):
        pass

    def load_data(self, file_path: str):
        """
        Load the data for a given day.
        Group the data by skipass id.
        """
        self.data = pd.read_csv(file_path)
        self.data['time'] = pd.to_datetime(
            self.data['time'], format=TIME_FORMAT)
        self.grouped_data = self.data.groupby('skipass')

    def process_skier(self, group: pd.DataFrame,
                      ) -> Optional[SkierData]:
        """
        Process data for a single skier, returns None if filtered out.
        """
        category = group['skier category'].iloc[0]
        skipass_category = group['skipass category'].iloc[0]

        group['time'] = group['time'].dt.floor('min')
        trajectory = dict(zip(group['time'], group['skilift']))

        injection_time: pd.Timestamp = min(trajectory.keys())
        leaving_time: pd.Timestamp = max(trajectory.keys())
        staying_time: pd.Timedelta = abs(leaving_time - injection_time)

        # Exclude skiers with just one skilift
        if len(trajectory) <= 1:
            return None
        # Exclude skiers arriving after 17:00
        if injection_time.time() > LATE_ARRIVAL_TIME:
            return None
        # Exclude skiers with a staying time less than 30 minutes
        if staying_time <= MIN_STAYING_TIME:
            return None
        # Exclude skiers with no category
        if category is np.nan:
            return None

        times = list(trajectory.keys())
        access = self._get_resort_access_skipass(category)
        interactions = []
        times_between_skilifts = pd.Timedelta(0)
        for i in range(len(times)-1):
            start_time = times[i]
            end_time = times[i + 1]
            skilift = trajectory[start_time]
            if i == 0:
                check_in_type = CheckInType.INJECTION
            else:
                check_in_type = None
            interaction = SkipassInteraction(start_time, skilift, access,
                                             check_in_type)
            interactions.append(interaction)
            times_between_skilifts = end_time - start_time

            # Exclude skiers with a min time between
            # skilifts less than 2 minutes
            if times_between_skilifts <= MIN_TIME_BETWEEN_SKILIFTS:
                return None

        check_out_interaction = SkipassInteraction(leaving_time,
                                                   trajectory[leaving_time],
                                                   access,
                                                   CheckInType.CHECK_OUT)
        interactions.append(check_out_interaction)

        skier = SkierData(category, skipass_category,
                          interactions, staying_time)

        return skier

    def _get_resort_access_skipass(self, category: str) -> str:
        """
        Set the skipass_resort_access based on the category.
        """
        if "domain 1" in category:
            return "DOMAIN 1"
        elif "domain 2" in category:
            return "DOMAIN 2"
        elif ("domain 1 and 2 " in category
              or "Carte Blanche" in category
              or "SKI O GRANDE" in category):
            return "DOMAIN 1 and 2"
        else:
            raise ValueError(f"Category {category} not found")

    def save_skier_data(self, skiers: list[SkierData]):
        """Save processed data to CSV files."""
        # Save skiers data
        skiers_df = pd.DataFrame([{
            'category': skier.skipass_category,
            'injection_time': skier.trajectory[0].time,
            'leaving_time': skier.trajectory[-1].time,
            'staying_time': skier.staying_time,
            'trajectory': [str(interaction) for
                           interaction in skier.trajectory],
            'trajectory_length': len(skier.trajectory),
        } for skier in skiers])
        skiers_df.to_csv(os.path.join(results_dir, 'skiers.csv'), index=False)
