from bintrees import RBTree

class ShowDates:
    """
    Internal helper for displaying the contents of an RBTree of dates.
    """
    @staticmethod
    def show_dates(tree: RBTree) -> None:
        """
        Print all dates stored in the tree.
        :param tree: RBTree containing dates as keys.
        :raises ValueError: If the tree is empty.
        :return: None
        """
        if tree.is_empty():
            raise ValueError("Tree is empty")

        for key in tree.keys():
            print(key)
