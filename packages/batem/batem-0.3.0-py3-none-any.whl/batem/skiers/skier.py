from enum import Enum
from typing import Optional
import pandas as pd


class CheckInType(Enum):
    INJECTION = "injection"
    CHECK_OUT = "check_out"


class SkipassInteraction:

    def __init__(self, time: pd.Timestamp, skilift: str, access: str,
                 check_in_type: Optional[CheckInType] = None):
        self.time = time
        self.skilift = skilift
        self.access = access
        self.check_in_type = check_in_type


class SkierData:
    def __init__(self, category: str, skipass_category: str,
                 trajectory: list[SkipassInteraction],
                 staying_time: pd.Timedelta):
        self.category = category
        self.skipass_category = skipass_category
        self.trajectory = trajectory
        self.staying_time = staying_time
