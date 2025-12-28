from datetime import datetime

class HelperMethods:
    """
    Collection of static helper methods used across the date_builder package.
    """
    @staticmethod
    def str_to_date(date: str) -> datetime.date:
        """
        Convert a date string into a datetime.date object.
        :param date: Date string in MM/DD/YYYY format.
        :raises ValueError: If the date string does not match the expected format.
        :return: A datetime.date object.
        """
        try:
            return datetime.strptime(date, "%m/%d/%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use dd/mm/yyyy format!")