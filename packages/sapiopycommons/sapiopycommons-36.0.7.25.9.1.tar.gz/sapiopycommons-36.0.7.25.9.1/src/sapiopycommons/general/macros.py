
import re
from datetime import datetime, timedelta, timezone

from sapiopycommons.general.exceptions import SapioException

date_macro_pattern: str = (
    r"@(?:today|yesterday|thisweek|"
    r"nextmonth|thismonth|lastmonth|"
    r"nextyear|thisyear|lastyear|"
    r"month(?:january|february|march|april|may|june|july|august|september|october|november|december)|"
    r"last\d+days|next\d+days)"
)
"""A regular expression that can be used to determine whether a given value matches one of the supported date macros."""

date_macro_values: list[str] = [
    "@today", "@yesterday", "@thisweek",
    "@nextmonth", "@thismonth", "@lastmonth",
    "@nextyear", "@thisyear", "@lastyear",
    "@monthjanuary", "@monthfebruary", "@monthmarch", "@monthapril", "@monthmay", "@monthjune", "@monthjuly",
    "@monthaugust", "@monthseptember", "@monthoctober", "@monthnovember", "@monthdecember",
    "@next_days", "@last_days"
]
"""A list of the supported date macros. For @next_days and @last_days, the underscore is expected to be replaced with
an integer."""


class MacroParser:
    """
    A utility class for parsing macros used in the Sapio platform.
    """
    _reg_month = re.compile(r"@\w*month\w*")
    _reg_digits = re.compile(r"@\w*(\d+)\w*")
    _reg_last_days = re.compile(r"@last(\d+)days")
    _reg_next_days = re.compile(r"@next(\d+)days")

    @staticmethod
    def _now() -> datetime:
        """
        :return: A datetime object for the current time in UTC.
        """
        return datetime.now(timezone.utc)

    @staticmethod
    def _dates_to_timestamps(a: datetime, b: datetime) -> tuple[int, int]:
        """
        Convert the given datetimes to epoch-millisecond timestamps on the start of the first date
        and the end of the second date.

        :param a: A datetime object.
        :param b: A datetime object.
        :return: A tuple containing the start and end timestamps in milliseconds since the epoch.
        """
        # The start of the date on the first datetime.
        a = a.replace(hour=0, minute=0, second=0, microsecond=0)
        # The end of the date on the second datetime.
        b = b.replace(hour=23, minute=59, second=59, microsecond=999000)
        return int(a.timestamp() * 1000), int(b.timestamp() * 1000)

    @classmethod
    def parse_date_macro(cls, macro: str) -> tuple[int, int]:
        """
        Convert a date macro string into a range of epoch millisecond timestamps.
        All macros are considered from the current time in UTC.

        :param macro: A valid date macro string. If an invalid macro is provided, an exception will be raised.
        :return: A tuple containing the start and end timestamps in milliseconds since the epoch for the given macro.
            The returned range is inclusive; the first value is the first millisecond of the starting date
            (00:00:00.000) and the last value is the final millisecond of the ending date (23:59:59.999).
        """
        if macro is None or not macro.strip():
            raise SapioException(f"Invalid macro. None or empty/blank string provided.")
        macro = macro.strip().lower()

        now: datetime = cls._now()

        # --- @today: 00:00:00.000 to 23:59:59.999 today ---
        if macro == "@today":
            return cls._dates_to_timestamps(now, now)

        # --- @yesterday: 00:00:00.000 to 23:59:59.999 yesterday ---
        if macro == "@yesterday":
            yesterday: datetime = now - timedelta(days=1)
            return cls._dates_to_timestamps(yesterday, yesterday)

        # --- @thisweek: Sunday -> Saturday (inclusive) ---
        if macro == "@thisweek":
            weekday: int = now.weekday()  # Monday=0 ... Sunday=6
            # TODO: Some way to control what the first day of the week is considered?
            #  +2 = Saturday
            #  +1 = Sunday
            #  +0 = Monday
            days_since_sunday: int = (weekday + 1) % 7
            sunday: datetime = now - timedelta(days=days_since_sunday)
            saturday: datetime = sunday + timedelta(days=6)
            return cls._dates_to_timestamps(sunday, saturday)

        # --- last/next N days ---
        if cls._reg_digits.fullmatch(macro):
            # --- @lastNdays ---
            if m := cls._reg_last_days.fullmatch(macro):
                days = int(m.group(1))
                return cls._dates_to_timestamps(now - timedelta(days=days), now)

            # --- @nextNdays ---
            if m := cls._reg_next_days.fullmatch(macro):
                days = int(m.group(1))
                return cls._dates_to_timestamps(now, now + timedelta(days=days))

            raise SapioException(f"Invalid macro: {macro}")

        # --- Month macros ---
        if cls._reg_month.fullmatch(macro):
            year: int = now.year
            month: int = now.month

            if macro == "@lastmonth":
                month -= 1
                if month == 0:
                    year -= 1
                    month = 12
            elif macro == "@nextmonth":
                month += 1
                if month == 13:
                    year += 1
                    month = 1
            # @thismonth uses the current month and year, so no replacement needed.
            elif macro != "@thismonth":
                month_map: dict[str, int] = {
                    "@monthjanuary": 1,
                    "@monthfebruary": 2,
                    "@monthmarch": 3,
                    "@monthapril": 4,
                    "@monthmay": 5,
                    "@monthjune": 6,
                    "@monthjuly": 7,
                    "@monthaugust": 8,
                    "@monthseptember": 9,
                    "@monthoctober": 10,
                    "@monthnovember": 11,
                    "@monthdecember": 12,
                }
                if macro in month_map:
                    month = month_map[macro]
                else:
                    raise SapioException(f"Invalid macro: {macro}")

            month_start: datetime = now.replace(year=year, month=month, day=1)
            # Find the first day of next month.
            if month == 12:
                next_month = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
            else:
                next_month = datetime(year, month + 1, 1, tzinfo=timezone.utc)
            # Then subtract one day to find the last day of the start month.
            month_end: datetime = next_month - timedelta(days=1)

            return cls._dates_to_timestamps(month_start, month_end)

        # --- Year macros ---
        if macro in ("@thisyear", "@lastyear", "@nextyear"):
            year: int = now.year
            if macro == "@lastyear":
                year -= 1
            elif macro == "@nextyear":
                year += 1
            # No change in year needed for @thisyear.

            year_start: datetime = now.replace(year=year, month=1, day=1)
            year_end: datetime = year_start.replace(year=year_start.year + 1) - timedelta(days=1)
            return cls._dates_to_timestamps(year_start, year_end)

        raise SapioException(f"Invalid macro: {macro}")
