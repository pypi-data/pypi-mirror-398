from bintrees import RBTree

from ._days_of_week import DaysOfWeek


class FilteredDates:
    """
    Internal helper for filtering dates from an RBTree based on year, month, day, and/or day of week.
    """

    def __init__(self, tree: RBTree, days_of_week: DaysOfWeek):
        """
        Construct a FilteredDates helper with the required dependencies.
        :param tree: Tree to filter from. Keys are expected to be datetime.date.
        :param days_of_week: DaysOfWeek instance controlling which weekdays are considered when filtering.
        """
        self.tree = tree
        self.days_of_week = days_of_week

    def _reset_days_of_week(self) -> None:
        """
        Reset the DaysOfWeek configuration to exclude all days. This is called after each filtering operation.
        """
        self.days_of_week.included_days(exclude_all=True)

    def filtered_date_range(self, days: list[int] = None, months: list[int] = None,
                            years: list[int] = None) -> RBTree:
        """
        Retrieve dates filtered by optional lists of days, months, years, and/or day of week. If the DaysOfWeek
        configuration has included weekdays, the date's weekday must also be one of those.
        :param days: Optional list of day-of-month values to filter by.
        :param months: Optional list of month values (1–12) to filter by.
        :param years: Optional list of year values to filter by.
        :raises ValueError: If no dates match the given filters.
        :return: A new RBTree containing only the filtered dates.
        """
        filtered_range: RBTree = RBTree()

        for key in self.tree.keys():
            # Filter by year
            if len(years) > 0 and key.year not in years:
                continue

            # Filter by month
            if len(months) > 0  and key.month not in months:
                continue

            # Filter by day of month
            if len(days) > 0 and key.day not in days:
                continue

            # Filter by day of week if any are configured
            included_weekdays = self.days_of_week.included
            if key.weekday() not in included_weekdays:
                continue

            # If the date meets all criteria insert into the filtered tree
            value: object = self.tree.get_value(key)
            filtered_range.insert(key, value)

        if len(filtered_range) == 0:
            raise ValueError("No filtered elements available")

        # Reset all days of week after each filtering call
        self._reset_days_of_week()

        return filtered_range

    def filtered_dates(self, day: int = None, month: int = None, year: int  = None) -> RBTree:
        """
        Retrieve dates filtered by optional single day, month, and/or year.
        :param day: Optional day-of-month to filter by.
        :param month: Optional month (1–12) to filter by.
        :param year: Optional year to filter by.
        :raises ValueError: If no dates match the given filters.
        :return: A new RBTree containing filtered dates.
        """
        years: list[int]  = []
        months: list[int] = []
        days: list[int] = []

        if year is not None:
            years = [year]

        if month is not None:
            months = [month]

        if day is not None:
            days = [day]

        return self.filtered_date_range(years=years, months=months, days=days)