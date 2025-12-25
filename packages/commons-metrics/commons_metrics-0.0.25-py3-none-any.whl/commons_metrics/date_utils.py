from datetime import datetime
from typing import List, Dict

from dateutil import parser


class DateUtils:
    """Utilidades para manejo de fechas y conversiones"""
    
    @staticmethod
    def parse_datetime(date_str: str) -> datetime:
        """
        Converts a string in ISO 8601 format to a datetime object.
        If the string is empty or None, it returns the current date and time with the time zone.

        Args:
            date_str(str): Date in ISO 8601 format (e.g., "2025-12-02T10:00:00+00:00").
        Returns:
            datetime: Datetime object corresponding to the string, or the current date if empty.
        """
        if not date_str:
            return datetime.now().astimezone()
        return parser.isoparse(date_str)

    @staticmethod
    def get_hours_difference_from_strings(start_date: str, end_date: str) -> float:
        """
        Calculate the difference in hours between two dates given as ISO 8601 strings.

        Args:
            start_date(str): Start date in ISO 8601 format.
            end_date(str): End date in ISO 8601 format.
        Returns:
            float: Difference in hours (can be negative if end_date < start_date).
        """
        start = DateUtils.parse_datetime(start_date)
        end = DateUtils.parse_datetime(end_date)
        return DateUtils.get_hours_difference(start, end)

    @staticmethod
    def get_hours_difference(start_date: datetime, end_date: datetime) -> float:
        """
        Calculate the difference in hours between two datetime objects.

        Args:
            start_date(datetime): Start date.
            end_date(datetime): End date.
        Returns:
            float: Difference in hours (can be negative if end_date < start_date).
        """
        return (end_date - start_date).total_seconds() / 3600

    @staticmethod
    def sort_by_date(list_dicts: List[Dict], date_attribute_name: str) -> List[Dict]:
        """
        Sorts a list of dictionaries by a specified date attribute in descending order.
        The method uses the `parse_datetime` function to convert date strings into datetime objects
        for accurate sorting.

        Args:
            list_dicts (List[Dict]): A list of dictionaries containing date attributes.
            date_attribute_name (str): The key name of the date attribute in each dictionary.
        Returns:
            List[Dict]: A new list of dictionaries sorted by the given date attribute in descending order.
        """
        return sorted(
            list_dicts,
            key=lambda x: DateUtils.parse_datetime(x.get(date_attribute_name)),
            reverse=True
        )
