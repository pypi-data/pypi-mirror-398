import datetime
from bintrees import RBTree

from ._date_exists import DateExists
from ._days_of_week import DaysOfWeek


class DeleteDates:
    """
    Internal helper for deleting single dates or date ranges from an RBTree.
    """

    def __init__(self, tree: RBTree, days_of_week: DaysOfWeek):
        """
        Initialize a DeleteDates helper.
        :param tree: The RBTree that stores dates as keys and values as associated objects.
        :param days_of_week: DaysOfWeek instance.
        """
        self.tree = tree
        self.days_of_week: DaysOfWeek = days_of_week
        self.find = DateExists()

    def delete_date(self, date: datetime.date) -> RBTree:
        """
        Delete a single date from the tree. If the date does not exist in the tree, a ValueError is raised.
        :param date: The date to be removed.
        :raises ValueError: If the date is not found in the tree.
        :return: The tree with the date removed.
        """
        if not self.find.date_exist(self.tree, date):
            raise ValueError("Date is not found in the tree")

        self.tree.remove(date)
        return self.tree

    def delete_date_range(self, lower_date: datetime.date = None, upper_date: datetime.date = None) -> RBTree:
        """
        Delete dates from the tree that fall within a given range.
        The range is inclusive:
            - If only lower_date is provided, deletes all dates >= lower_date.
            - If only upper_date is provided, deletes all dates <= upper_date.
            - If both are provided, deletes all dates with lower_date <= date <= upper_date.

        :param lower_date: Lower bound of dates to be deleted (inclusive).
        :param upper_date: Upper bound of dates to be deleted (inclusive).
        :raises ValueError: If both lower_date and upper_date are None.
        :return: The tree with the specified dates removed.
        """
        if self.tree.is_empty():
            raise ValueError("Can not delete from empty tree")

        if lower_date is None and upper_date is None:
            raise ValueError("Both lower_date and upper_date cannot be None")

        if lower_date is not None and upper_date is not None:
            if lower_date > upper_date:
                raise ValueError(f"Lower date must be less than or equal to upper date")

        keys_to_delete: list[datetime.date] = []

        for key in self.tree.keys():
            # If lower bound exists and key is below it continue to next iteration
            if lower_date is not None and key < lower_date:
                continue

            # If upper bound exists and key is above it break from loop
            if upper_date is not None and key > upper_date:
                break
            # Add keys to be deleted to list
            keys_to_delete.append(key)

        # Delete elements from tree
        for key in keys_to_delete:
            self.tree.remove(key)

        return self.tree