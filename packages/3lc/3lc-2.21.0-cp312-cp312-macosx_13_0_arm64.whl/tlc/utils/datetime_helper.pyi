import datetime

class DateTimeHelper:
    """
    A class with helper methods for working with timestamps
    """
    @staticmethod
    def compare_timestamps(timestamp_1: str | datetime.datetime | None, timestamp_2: str | datetime.datetime) -> datetime.timedelta:
        """Compare timestamps with time zone information.

        The function parses the timestamps and computes a difference in seconds.

        :param timestamp_1: The first timestamp to compare.
        :param timestamp_2: The second timestamp to compare.
        :returns: The difference in seconds between the timestamps. A positive value indicates that timestamp_1 is
            later than timestamp_2.
        :raises ValueError: if the timestamp is invalid.
        """
