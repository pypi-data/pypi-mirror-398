import datetime

from bintrees import RBTree

from ._days_of_week import DaysOfWeek

class AddDates:
    """
    Internal helper for inserting single dates or date ranges into an RBTree.
    """
    def __init__(self, date_obj: object, tree: RBTree, days_of_week: DaysOfWeek):
        """
        Initialize an AddDates helper.
        :param date_obj: Default value to associate with dates when a unique object is not provided.
        :param tree: RBTree that stores dates as keys and arbitrary values.
        :param days_of_week: DaysOfWeek instance controlling which weekdays are eligible to be added.
        """
        self.date_obj = date_obj
        self.tree = tree
        self.days_of_week: DaysOfWeek = days_of_week

    def _reset_days_of_week(self) -> None:
        """
        Reset the DaysOfWeek configuration to exclude all days.
        :returns: None
        """
        self.days_of_week.included_days(exclude_all=True)

    def _copy_obj(self) -> object:
        """
         Create a shallow copy of the default date_obj.
         :returns: Returns the shallow copy.
         """
        copy: object = self.date_obj
        return copy

    def add_date(self, first_date: datetime.date, last_date: datetime.date = None) -> RBTree:
        """
        Adds one or more dates to the tree. Adds dates between first_date and last_date (inclusive). If last_date is not
        provided, only first_date is added. Dates are used as keys in the RBTree. The associated value is either the
        default date_obj.
        :param first_date: The first date to add to the tree.
        :param last_date: The last date to add to the tree (inclusive). If None, only first_date is added.
        :raises ValueError: If last_date is earlier than first_date, or if no days of week have been included via
        DaysOfWeek.
        :return: The tree with the added dates.
        """
        # Checks for single date entry occurring by lack of last date
        if last_date is None:
            last_date = first_date

        if last_date < first_date:
            raise ValueError()

        if len(self.days_of_week.included_days_list) == 0:
            raise ValueError("No days of weeks were included")

        current_date: datetime.date = first_date
        while current_date <= last_date:
            if current_date.weekday() in self.days_of_week.included:

               # Inserts date into the tree
                self.tree.insert(current_date, self._copy_obj())

            current_date = current_date + datetime.timedelta(1)

        # Resets the days of week to be added to be False for each day
        self._reset_days_of_week()

        return self.tree


