"""
    date_tree.py

    This module provides the DateTree class, a high level interface for
    managing, filtering, and querying collections of dates stored in a
    Red-Black Tree (RBTree).

    The DateTree encapsulates common date based operations such as:
    - Adding single dates or ranges of dates
    - Deleting individual dates or ranges of dates
    - Filtering dates by day, month, year, or day of week
    - Traversing and displaying stored dates in sorted order

    Dates are stored as keys in an RBTree, ensuring:
    - O(log n) insertion and deletion
    - Deterministic, sorted traversal
    - Efficient range queries

    Typical usage:

        from bintrees import RBTree
        from date_tree.date_builder import DateTree

        tree = RBTree()
        builder = DateTree(tree, date_obj="example")

        builder.include_days_of_week(monday=True, friday=True)
        builder.add_dates(date(2025, 1, 1), date(2025, 1, 31))
        filtered = builder.filter_dates(month=1, year=2025)

    Exceptions raised by helper classes (such as ValueError for invalid
    operations) are propagated through the DateTree API and documented
    on individual methods.
    """
from datetime import datetime

from bintrees import RBTree

from ._filter_dates import FilteredDates
from ._days_of_week import DaysOfWeek
from ._delete_dates import DeleteDates
from ._date_exists import DateExists
from ._add_dates import AddDates
from ._helper_methods import HelperMethods
from ._show_dates import ShowDates

class DateTree:
    """
        High-level interface for storing and manipulating dates in an RBTree.

        DateTree uses a RBTree of dates and provides methods for
        adding dates or date ranges, deleting dates, and filtering dates by
        day, month, year, and day of week.
        """
    def __init__(self, tree: RBTree, date_obj: object):
        """
        Create a new DateTree.

        :param tree: RBTree instance used to store dates as keys.
        :param date_obj: Default value to associate with dates.
        """
        self._date_obj = date_obj
        self._tree = tree
        self._days_of_week: DaysOfWeek = DaysOfWeek()
        self._exists = DateExists()

    @property
    def date_obj(self) -> object:
        """
        Gets the date object to be used as the value.
        :return: The date object
        """
        return self._date_obj

    @property
    def tree(self) -> RBTree:
        """
        Gets the instance of the RBTree.
        :return: Returns the instance of the RBTree containing its elements.
        """
        return self._tree

    @property
    def included_days(self) -> list[int]:
        """
        Gets the list of days of the week that have been included by user.
        :return: Returns the list of days of the week.
        """
        return self._days_of_week.included

    @property
    def count(self) -> int:
        """
        Keeps track of the number of elements in the tree.
        :return: The number of elements in the tree.
        """
        return len(self._tree)

    @property
    def is_empty(self) -> bool:
        """
        Returns a bool value to check if tree is empty.
        :return: True if tree is empty and False if tree is not empty.
        """
        return self._tree.is_empty()

    def add_dates(self, first_date: datetime.date, last_date: datetime.date = None) -> RBTree:
        """
        Adds dates desired dates to the tree

        :param first_date: The first date to add to the tree.
        :param last_date: The last date to add to the tree.
        :raises ValueError: Raised if first date is less than last date, or no days of week have been added.

        Recommended Usage:
            Parameter usage:
                add_dates(first_date): adds just one date to the tree.
                add_dates(first_date, last_date): adds dates in the range between the first and last dates inclusive of
                                                  the first and last dates.

            General Usage:
                - IMPORTANT: At least one day of week must be included to add dates. If at least one is not include a
                             ValueError Exception will be raised.

        :return: The tree with the added dates.
        """
        return AddDates(self._date_obj, self._tree, self._days_of_week).add_date(first_date, last_date)

    def date_existance(self, tree: RBTree, date: datetime.date) -> bool:
        """
        Checks if a date exists in the tree and returns True if the date exists and False if the date does not exist.
        :param tree: Tree where the dates are stored.
        :param date: The date being searched for.
        :return: Bool response if the date has been found.
        """
        return self._exists.date_exist(tree, date)

    def delete_date(self, date: datetime.date) -> RBTree:
        """
        Deletes a single date from the tree if the date exists within the tree. If the date does not exist then a
        value error is raised.
        :param date: The date to be removed.
        :raises ValueError: Raised if date does not exist in tree.
        :return: The tree with the date removed.
        """
        return DeleteDates(self._tree, self._days_of_week).delete_date(date)

    def delete_date_range(self, lower_date: datetime.date = None, upper_date: datetime.date = None) -> RBTree:
        """
        Deletes a range of dates from the tree.
        :param lower_date: Lower bound of dates to be deleted.
        :param upper_date: Upper bound of dates to be deleted.
        :raises ValueError: Raised if no arguments are passed

        Recommended Usage:
            Parameter usage:
                delete_date_range(lower_date): All dates in tree greater than or equal to lower date will be deleted
                delete_date_range(upper_date): All dates in tree less than or equal to upper date will be deleted
                delete_date_range(lower_date, upper_date): All dates in tree between lower date and upper date
                                                          (inclusive) will be deleted from the tree

        :return: Returns a tree without the deleted dates
        """
        return DeleteDates(self._tree, self._days_of_week).delete_date_range(lower_date, upper_date)


    def filter_dates(self, day: int = None, month: int = None, year: int = None) -> RBTree:
        """
        Retrieve dates filtered by optional month, day, day of week, and/or year.

        :param day: Day to be included.
        :param month: Month to be included.
        :param year: Year to be included.
        :raises ValueError: Raised if no days of week have been added

        Recommended usage:
            Parameter usage examples:
                get_dates(month=1, year=2020): Includes all dates in January 2020.
                get_dates(year=2020, month=1): Includes all dates in January 2020.
                get_dates(year=2020): Includes all dates in 2020.
                etc...

            General usage information:
                - Filtering by 3 parameters (day, month, year) will provide a tree of a specified date.
                - Filtering by 4 parameters (day, day of week, month, year) may provide and empty tree.
                - Filtering by day of week can be combined with month and year will provide all instances of that day
                  of the week.
                    -- TO FILTER BY DAY OF WEEK: User must add the days of the week by using the DaysOfWeek class which
                       can be accessed by calling the days_of_week field. See DaysOfWeek class for documentation.
                    -- IMPORTANT: At least one day of week must be included to add dates. If at least one is not
                                  include a ValueError Exception will be raised.
                - Filtering by day and year for example get_dates(day=1, year=2020) will provide a tree containing the
                  1st of the month for every month in the year.
                - Filtering by month and year for example get_dates(month=1, year=2020) will add all dates in january
                  2020 to a tree.

        :return: A new tree containing filtered dates.
        """
        return FilteredDates(self._tree, self._days_of_week).filtered_dates(day=day, month=month, year=year)

    def filtered_date_range(self, days: list[int] = None, months: list[int] = None,
                                years: list[int] = None) -> RBTree:
        """
        Retrieve range of dates filtered by optional month, day, day of week, and/or year.

        :param days: List of days to include.
        :param months: List of Months to include.
        :param years: List of years to include.
        :raises ValueError: Raised if no days of week have been added.

        Recommended usage:
            Parameter usage:
                get_date_range(months=[11, 12], years=[1999, 2020], days=[1]): Will include the first of the month for
                        December and November in 1999 and 2020
                get_date_range(months=[11, 12], years=[1999, 2020]): Will include all days in the months of December
                    and November in 1999 and 2020
                get_date_range(years=[2020]): Includes all days in 2020
                etc...

            General usage information:
                - Filtering by 3 parameters (day, month, year) will provide a tree of a specified date.
                - Filtering by 4 parameters (day, day of week, month, year) may provide and empty tree.
                - Filtering by day of week can be combined with month and year will provide all instances of that day
                  of the week.
                    -- TO FILTER BY DAY OF WEEK: User must add the days of the week by using the DaysOfWeek class which
                       can be accessed by calling the days_of_week field. See DaysOfWeek class for documentation.
                    -- IMPORTANT: At least one day of week must be included to add dates. If at least one is not
                                  include a ValueError Exception will be raised.

        :return: A new tree containing filtered dates.
        """
        return FilteredDates(self._tree, self._days_of_week).filtered_date_range(days=days, months=months, years=years)

    def include_days_of_week(self, monday=False, tuesday=False, wednesday=False, thursday=False, friday=False,
                             saturday=False, sunday=False, include_all=False, exclude_all=False) -> None:
        """
        Includes or exclude days on the week based on if the argument is set to True or False.
        :param monday: If marked True includes monday.
        :param tuesday: If marked True includes tuesday.
        :param wednesday: If marked True includes wednesday.
        :param thursday: If marked True includes thursday.
        :param friday: If marked True includes friday.
        :param saturday: If marked True includes saturday.
        :param sunday: If marked True includes sunday.
        :param include_all: If marked True includes all days of week.
        :param exclude_all: If marked True excludes all days of week.
        :return: None
        """
        self._days_of_week.included_days(monday, tuesday, wednesday, thursday, friday, saturday, sunday, include_all,
                                         exclude_all)

    @staticmethod
    def display_dates(tree: RBTree) -> None:
        """
        Prints the dates in the tree to the terminal to provide user with a visual representation of the dates added.
        :return: None
        """
        ShowDates.show_dates(tree)

    @staticmethod
    def str_to_date(date_str: str) -> datetime.date:
        """
        Converts string form of date to date.
        :param date_str: string date in dd/mm/yyyy format.
        :return: Date as a datetime object.
        """
        return HelperMethods.str_to_date(date_str)

