from __future__ import annotations

import time
from datetime import datetime
from typing import Any

import pytz

from sapiopycommons.general.exceptions import SapioException

__timezone = None
"""The default timezone. Use TimeUtil.set_default_timezone in a global context before making use of TimeUtil."""


# FR-46064 - Initial port of PyWebhookUtils to sapiopycommons.
class TimeUtil:
    """
    A class that contains various date/time related utility methods. All times are based off of the timezone from
    the timezone() function. The default timezone is set by the timezone variable above this class definition.
    Since this is a global variable, every endpoint from the same server instance will use it. If you need to change
    the timezone, then call TimeUtil.set_default_timezone() somewhere in a global context in your server. A list of
    valid timezones can be found at https://en.wikipedia.org/wiki/List_of_tz_database_time_zones.

    If a timezone that is different from the default is needed but you don't want to change the default, a timezone name
    or UTC offset in seconds may be provided to each function. A UTC offset can be found at
    context.user.session_additional_data.utc_offset_seconds.

    Note that static date fields display their time in UTC instead of in whatever the server's time is. So when dealing
    with static date fields, use "UTC" as your input timezone.
    """
    @staticmethod
    def get_default_timezone() -> Any:
        """
        Returns the timezone that TimeUtil is currently using as its default.
        """
        global __timezone
        return __timezone

    @staticmethod
    def set_default_timezone(new_timezone: str | int) -> None:
        """
        Set the timezone used by TimeUtil to something new.

        :param new_timezone: The timezone to set the default to. A list of valid timezones can be found at
            https://en.wikipedia.org/wiki/List_of_tz_database_time_zones. May also accept a UTC offset in seconds.
        """
        global __timezone
        __timezone = TimeUtil.__to_tz(new_timezone)

    @staticmethod
    def __to_tz(timezone: str | int = None) -> Any:
        """
        :param timezone: Either the name of a timezone, a UTC offset in seconds, or None if the default should be used.
        :return: The timezone object to use for the given input. If the input is None, uses the default timezone.
        """
        if isinstance(timezone, str):
            # PR-46571: Convert timezones to a UTC offset and then use that offset as the timezone. This is necessary
            # because pytz may return timezones from strings in Local Mean Time instead of a timezone with a UTC offset.
            # LMT may be a few minutes off of the actual time in that timezone right now.
            # https://stackoverflow.com/questions/35462876
            offset: int = TimeUtil.__get_timezone_offset(timezone)
            # This function takes an offset in minutes, so divide the provided offset seconds by 60.
            return pytz.FixedOffset(offset // 60)
        if isinstance(timezone, int):
            return pytz.FixedOffset(timezone // 60)
        if timezone is None:
            return TimeUtil.get_default_timezone()
        raise SapioException(f"Unhandled timezone object of type {type(timezone)}: {timezone}")

    @staticmethod
    def __get_timezone_offset(timezone: str | int | None) -> int:
        """
        :param timezone: Either the name of a timezone, a UTC offset in seconds, or None if the default should be used.
        :return: The UTC offset in seconds of the provided timezone.
        """
        if isinstance(timezone, int):
            return timezone
        if isinstance(timezone, str):
            timezone = pytz.timezone(timezone)
        if timezone is None:
            timezone = TimeUtil.get_default_timezone()
        return int(datetime.now(timezone).utcoffset().total_seconds())

    @staticmethod
    def current_time(timezone: str | int = None) -> datetime:
        """
        The current time as a datetime object.

        :param timezone: The timezone to initialize the current time with. If no timezone is provided, uses the global
            timezone variable set by the TimeUtil. A list of valid timezones can be found at
            https://en.wikipedia.org/wiki/List_of_tz_database_time_zones. May also accept a UTC offset in seconds.
        """
        tz = TimeUtil.__to_tz(timezone)
        return datetime.now(tz)

    @staticmethod
    def now_in_millis() -> int:
        """
        The current time in milliseconds since the epoch.
        """
        return round(time.time() * 1000)

    @staticmethod
    def now_in_format(time_format: str, timezone: str | int = None) -> str:
        """
        The current time in some date format.

        :param time_format: The format to display the current time in. Documentation for how the time formatting works
            can be found at https://docs.python.org/3.10/library/datetime.html#strftime-and-strptime-behavior
        :param timezone: The timezone to initialize the current time with. If no timezone is provided, uses the global
            timezone variable set by the TimeUtil. A list of valid timezones can be found at
            https://en.wikipedia.org/wiki/List_of_tz_database_time_zones. May also accept a UTC offset in seconds.
        """
        return TimeUtil.current_time(timezone).strftime(time_format)

    @staticmethod
    def millis_to_format(millis: int, time_format: str, timezone: str | int = None) -> str | None:
        """
        Convert the input time in milliseconds to the provided format. If None is passed to the millis parameter,
        None will be returned

        :param millis: The time in milliseconds to convert from.
        :param time_format: The format to display the input time in. Documentation for how the time formatting works
            can be found at https://docs.python.org/3.10/library/datetime.html#strftime-and-strptime-behavior
        :param timezone: The timezone to initialize the current time with. If no timezone is provided, uses the global
            timezone variable set by the TimeUtil. A list of valid timezones can be found at
            https://en.wikipedia.org/wiki/List_of_tz_database_time_zones. May also accept a UTC offset in seconds.
        """
        if millis is None:
            return None

        tz = TimeUtil.__to_tz(timezone)
        return datetime.fromtimestamp(millis / 1000, tz).strftime(time_format)

    @staticmethod
    def format_to_millis(time_point: str, time_format: str, timezone: str | int = None) -> int | None:
        """
        Convert the input time from the provided format to milliseconds. If None is passed to the time_point parameter,
        None will be returned.

        :param time_point: The time in some date/time format to convert from.
        :param time_format: The format that the time_point is in. Documentation for how the time formatting works
            can be found at https://docs.python.org/3.10/library/datetime.html#strftime-and-strptime-behavior
        :param timezone: The timezone to initialize the current time with. If no timezone is provided, uses the global
            timezone variable set by the TimeUtil. A list of valid timezones can be found at
            https://en.wikipedia.org/wiki/List_of_tz_database_time_zones. May also accept a UTC offset in seconds.
        """
        if time_point is None:
            return None

        tz = TimeUtil.__to_tz(timezone)
        return int(datetime.strptime(time_point, time_format).replace(tzinfo=tz).timestamp() * 1000)

    # FR-47296: Provide functions for shifting between timezones.
    @staticmethod
    def shift_now(to_timezone: str = "UTC", from_timezone: str | None = None) -> int:
        """
        Take the current time in from_timezone and output the epoch timestamp that would display that same time in
        to_timezone. A use case for this is when dealing with static date fields to convert a provided timestamp to the
        value necessary to display that timestamp in the same way when viewed in the static date field.

        :param to_timezone: The timezone to shift to. If not provided, uses UTC.
        :param from_timezone: The timezone to shift from. If no timezone is provided, uses the global
            timezone variable set by the TimeUtil. A list of valid timezones can be found at
            https://en.wikipedia.org/wiki/List_of_tz_database_time_zones. May also accept a UTC offset in seconds.
        :return: The epoch timestamp that would display as the same time in to_timezone as the current time in
            from_timezone.
        """
        millis: int = TimeUtil.now_in_millis()
        return TimeUtil.shift_millis(millis, to_timezone, from_timezone)

    @staticmethod
    def shift_millis(millis: int, to_timezone: str = "UTC", from_timezone: str | None = None) -> int | None:
        """
        Take a number of milliseconds for a time in from_timezone and output the epoch timestamp that would display that
        same time in to_timezone. A use case for this is when dealing with static date fields to convert a provided
        timestamp to the value necessary to display that timestamp in the same way when viewed in the static date field.
        If None is passed to the millis parameter, None will be returned.

        :param millis: The time in milliseconds to convert from.
        :param to_timezone: The timezone to shift to. If not provided, uses UTC.
        :param from_timezone: The timezone to shift from. If no timezone is provided, uses the global
            timezone variable set by the TimeUtil. A list of valid timezones can be found at
            https://en.wikipedia.org/wiki/List_of_tz_database_time_zones. May also accept a UTC offset in seconds.
        :return: The epoch timestamp that would display as the same time in to_timezone as the given time in
            from_timezone.
        """
        if millis is None:
            return None

        to_offset: int = TimeUtil.__get_timezone_offset(to_timezone) * 1000
        from_offset: int = TimeUtil.__get_timezone_offset(from_timezone) * 1000
        return millis + from_offset - to_offset

    @staticmethod
    def shift_format(time_point: str, time_format: str, to_timezone: str = "UTC", from_timezone: str | None = None) \
            -> int | None:
        """
        Take a timestamp for a time in from_timezone and output the epoch timestamp that would display that same time
        in to_timezone. A use case for this is when dealing with static date fields to convert a provided timestamp to
        the value necessary to display that timestamp in the same way when viewed in the static date field.
        If None is passed to the time_point parameter, None will be returned.

        :param time_point: The time in some date/time format to convert from.
        :param time_format: The format that the time_point is in. Documentation for how the time formatting works
            can be found at https://docs.python.org/3.10/library/datetime.html#strftime-and-strptime-behavior
        :param to_timezone: The timezone to shift to. If not provided, uses UTC.
        :param from_timezone: The timezone to shift from. If no timezone is provided, uses the global
            timezone variable set by the TimeUtil. A list of valid timezones can be found at
            https://en.wikipedia.org/wiki/List_of_tz_database_time_zones. May also accept a UTC offset in seconds.
        :return: The epoch timestamp that would display as the same time in to_timezone as the given time in
            from_timezone.
        """
        if time_point is None:
            return None

        millis: int = TimeUtil.format_to_millis(time_point, time_format, from_timezone)
        return TimeUtil.shift_millis(millis, to_timezone, from_timezone)

    # FR-46154: Create a function that determines if a string matches a time format.
    @staticmethod
    def str_matches_format(time_point: str, time_format: str) -> bool:
        """
        Determine if the given string is recognized as a valid time in the given format.

        :param time_point: The time in some date/time format to check.
        :param time_format: The format that the time_point should be in. Documentation for how the time formatting works
            can be found at https://docs.python.org/3.10/library/datetime.html#strftime-and-strptime-behavior
        """
        if time_point is None:
            return False
        try:
            # If this function successfully runs, then the time_point matches the time_format.
            TimeUtil.format_to_millis(time_point, time_format, "UTC")
            return True
        except Exception:
            return False


MILLISECONDS_IN_A_SECOND: int = 1000
MILLISECONDS_IN_A_MINUTE: int = 60 * MILLISECONDS_IN_A_SECOND
MILLISECONDS_IN_AN_HOUR: int = 60 * MILLISECONDS_IN_A_MINUTE
MILLISECONDS_IN_A_DAY: int = 24 * MILLISECONDS_IN_AN_HOUR

class ElapsedTime:
    _start: int
    _end: int

    _total_days: float
    _total_hours: float
    _total_minutes: float
    _total_seconds: float
    _total_milliseconds: int

    _days: int
    _hours: int
    _minutes: int
    _seconds: int
    _milliseconds: int

    def __init__(self, start: int | float, end: int | float | None = None):
        """
        :param start: The start timestamp in milliseconds (int) or seconds (float).
        :param end: The end timestamp in milliseconds (int) or seconds (float). If None, uses the current epoch time in
            milliseconds.
        """
        if isinstance(start, float):
            start = int(start * 1000)

        if end is None:
            end = TimeUtil.now_in_millis()
        elif isinstance(end, float):
            end = int(end * 1000)

        self._start = start
        self._end = end

        self._total_milliseconds = end - start
        self._total_seconds = self._total_milliseconds / MILLISECONDS_IN_A_SECOND
        self._total_minutes = self._total_milliseconds / MILLISECONDS_IN_A_MINUTE
        self._total_hours = self._total_milliseconds / MILLISECONDS_IN_AN_HOUR
        self._total_days = self._total_milliseconds / MILLISECONDS_IN_A_DAY

        elapsed: int = end - start
        self._days: int = elapsed // MILLISECONDS_IN_A_DAY
        elapsed -= self._days * MILLISECONDS_IN_A_DAY
        self._hours: int = elapsed // MILLISECONDS_IN_AN_HOUR
        elapsed -= self._hours * MILLISECONDS_IN_AN_HOUR
        self._minutes: int = elapsed // MILLISECONDS_IN_A_MINUTE
        elapsed -= self._minutes * MILLISECONDS_IN_A_MINUTE
        self._seconds: int = elapsed // MILLISECONDS_IN_A_SECOND
        elapsed -= self._seconds * MILLISECONDS_IN_A_SECOND
        self._milliseconds = elapsed

    @staticmethod
    def as_eta(total: int, progress: int, start: int | float, now: int | float | None = None) -> ElapsedTime:
        """
        Calculate the estimated time remaining for a task based on how much time has passed so far and how many items
        have been completed. The estimated time remaining is calculated by determining the average time per item
        completed so far and multiplying that by the number of items remaining.

        :param total: The total number of items that need to be completed for the task.
        :param progress: The number of items that have been completed so far.
        :param start: The start time of a task in milliseconds (int) or seconds (float).
        :param now: The amount of time that has passed so far while performing the task in milliseconds (int)
            or seconds (float). If None, uses the current epoch time in milliseconds.
        :return: An ElapsedTime object representing the estimated time remaining.
        """
        if now is None:
            now = TimeUtil.now_in_millis()
        is_int: bool = isinstance(start, int) and isinstance(now, int)
        # How much time has elapsed so far.
        elapsed: int | float = now - start
        # The average time it has taken to complete each record so far.
        per_record: int | float = (elapsed // progress) if is_int else (elapsed / progress)
        # The estimated time remaining based on the average time per record.
        remaining: int | float = (total - progress) * per_record
        return ElapsedTime(now, now + remaining)

    def __str__(self) -> str:
        time_str: str = f"{self._hours:02d}:{self._minutes:02d}:{self._seconds:02d}.{self._milliseconds:03d}"
        if self._days:
            return f"{self._days}d {time_str}"
        return time_str

    @property
    def start(self) -> int:
        """
        The start timestamp in milliseconds.
        """
        return self._start

    @property
    def end(self) -> int:
        """
        The end timestamp in milliseconds.
        """
        return self._end

    @property
    def total_days(self) -> float:
        """
        The total number of days in the elapsed time. For example, an elapsed time of 1.5 days would
        return 1.5.
        """
        return self._total_days

    @property
    def total_hours(self) -> float:
        """
        The total number of hours in the elapsed time. For example, an elapsed time of 1.5 days would
        return 36.0.
        """
        return self._total_hours

    @property
    def total_minutes(self) -> float:
        """
        The total number of minutes in the elapsed time. For example, an elapsed time of 1.5 days would
        return 2,160.0.
        """
        return self._total_minutes

    @property
    def total_seconds(self) -> float:
        """
        The total number of seconds in the elapsed time. For example, an elapsed time of 1.5 days would
        return 129,600.0.
        """
        return self._total_seconds

    @property
    def total_milliseconds(self) -> int:
        """
        The total number of milliseconds in the elapsed time. For example, an elapsed time of 1.5 days would
        return 129,600,000.
        """
        return self._total_milliseconds

    @property
    def days(self) -> int:
        """
        The number of full days in the elapsed time. For example, an elapsed time of 1.5 days would
        return 1.
        """
        return self._days

    @property
    def hours(self) -> int:
        """
        The number of full hours in the elapsed time, not counting full days. For example, an elapsed time of 1.5 days
        would return 12.
        """
        return self._hours

    @property
    def minutes(self) -> int:
        """
        The number of full minutes in the elapsed time, not counting full hours. For example, an elapsed time of
        1.5 hours would return 30.
        """
        return self._minutes

    @property
    def seconds(self) -> int:
        """
        The number of full seconds in the elapsed time, not counting full minutes. For example, an elapsed time of 1
        minute and 45 seconds would return 45.
        """
        return self._seconds

    @property
    def milliseconds(self) -> int:
        """
        The number of milliseconds in the elapsed time, not counting full seconds. For example, an elapsed time of
        1.25 seconds would return 250.
        """
        return self._milliseconds
