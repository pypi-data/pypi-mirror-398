import datetime

from bintrees import RBTree

class DateExists:
    """
    Internal helper for checking whether a given date exists in an RBTree.
    """
    @staticmethod
    def date_exist(tree: RBTree, date: datetime.date) -> bool:
        """
        Check whether the given date exists in the tree.
        :param tree: The tree to be searched. Keys are expected to be datetime.date.
        :param date: The date being searched for.
        :raises ValueError: Raises if invalid date type
        :return: True if the date exists in the tree, False otherwise.
        """
        if isinstance(date, datetime.date):
            return date in tree.keys()
        else:
            raise ValueError("Invalid date type. Date must be of type datetime.date")
