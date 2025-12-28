
class DaysOfWeek:
    """
    Manage a set of included weekdays represented as integers 0–6. Weekdays follow the datetime convention:
    0 = Monday, 1 = Tuesday, ..., 6 = Sunday. The included_days_list field stores the indices of weekdays that are
    currently enabled for operations such as adding or filtering dates.
    """
    def __init__(self):
        """
        Initialize with no days of the week included.
        """
        self.included_days_list: list[int] = []

    @property
    def included(self) -> list[int]:
        """
        Return the list of included weekdays.
        :return: A list of integers representing included weekdays (0 = Monday, ..., 6 = Sunday).
        """
        return self.included_days_list

    def _include_exclude_check(self, days_list: list[bool], action: str) -> None:
        """
        Validate that no specific days are marked True when using an include_all or exclude_all action.
        :param days_list: List of booleans indicating which days are set.
        :param action: The action being performed ("include" or "exclude").
        :raises ValueError: If both the global {action}_all flag and any specific day are marked True.
        """
        for each in days_list:
            if each is True:
                raise ValueError(f"Marking both {action} all and a specific day as True is invalid, if the intent is "
                                 f"to {action} all only mark {action}_all as True")

    def _include_all(self, days_list: list[bool]) -> None:
        """
        Includes all the days of the week
        :param days_list: List used to check for conflicting specific days.
        :return: None
        """
        self._include_exclude_check(days_list, "include")
        for i in range(0, 7):
            self.included_days_list.append(i)

    def _exclude_all(self, days_list: list[bool]) -> None:
        """
        Excludes all the days of the week
        :param days_list: List used to check for conflicting specific days.
        :return: None
        """
        self._include_exclude_check(days_list, "exclude")
        self.included_days_list.clear()

    def included_days(self, monday=False, tuesday=False, wednesday=False, thursday=False, friday=False, saturday=False,
                     sunday=None, include_all=False, exclude_all=False) -> None:
        """
        Include or exclude days of the week based on the provided flags.

        :param monday: If True, include Monday.
        :param tuesday: If True, include Tuesday.
        :param wednesday: If True, include Wednesday.
        :param thursday: If True, include Thursday.
        :param friday: If True, include Friday.
        :param saturday: If True, include Saturday.
        :param sunday: If True, include Sunday.
        :param include_all: If True, include all days of the week.
        :param exclude_all: If True, exclude all days of the week.
        :raises ValueError: If both include_all and exclude_all are True.
        """
        days: list[bool] = [monday, tuesday, wednesday, thursday, friday, saturday, sunday]

        # Makes sure include and exclude all are not both marked as True
        if include_all is True and exclude_all is True:
            raise ValueError("Can not mark both include_all and exclude_all as True")

        # Action for including all
        if include_all is True:
            self._include_all(days)

        # Action for excluding all
        elif exclude_all is True:
            self._exclude_all(days)

        else:
            # Includes particular days of week
            for i in range(len(days)):
                if days[i] is True:
                    self.included_days_list.append(i)





