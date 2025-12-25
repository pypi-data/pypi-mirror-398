import datetime

from ...utils import current_date


class TimeFilter:
    """
    Holds day and optional hours range to manage time filtering in ExtractionQueries
    Provides a default time filter (previous day)
    """

    def __init__(
        self,
        day: datetime.date,
        hour_min: int | None = None,
        hour_max: int | None = None,
    ):
        self.day = day
        self.hour_min = hour_min
        self.hour_max = hour_max

    @classmethod
    def default(cls):
        """
        Default time filter for extraction:
        - day = yesterday
        - hours = [0,23]
        """
        yesterday = current_date() - datetime.timedelta(days=1)
        return cls(day=yesterday, hour_min=0, hour_max=23)

    def to_dict(self) -> dict:
        return {
            "day": self.day,
            "hour_min": self.hour_min,
            "hour_max": self.hour_max,
        }
