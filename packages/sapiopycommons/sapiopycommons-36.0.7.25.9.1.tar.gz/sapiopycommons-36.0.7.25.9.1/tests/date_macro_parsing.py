import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from sapiopycommons.general.exceptions import SapioException

from sapiopycommons.general.macros import MacroParser


def dt_utc(y, m, d, h=0, mi=0, s=0, ms=0):
    """Helper to create a UTC datetime."""
    return datetime(y, m, d, h, mi, s, ms * 1000, tzinfo=timezone.utc)


def to_ms(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


class TestMacroParser(unittest.TestCase):
    # Fixed "today" for all tests: 2025-02-14 00:00:00 UTC
    FIXED_TODAY = dt_utc(2025, 2, 14)

    @staticmethod
    def _end_of_day(dt: datetime) -> datetime:
        return dt.replace(hour=23, minute=59, second=59, microsecond=999000)

    def _patch_today(self):
        """
        Patch MacroParser._now to always return FIXED_TODAY.
        This keeps all tests deterministic.
        """
        return patch.object(
            MacroParser,
            "_now",
            return_value=self.FIXED_TODAY,
        )

    # ------------------------------
    # Basic macros
    # ------------------------------

    def test_today(self):
        with self._patch_today():
            begin, end = MacroParser.parse_date_macro("@today")
        expected_begin = to_ms(self.FIXED_TODAY)
        expected_end = to_ms(self._end_of_day(self.FIXED_TODAY))
        self.assertEqual((begin, end), (expected_begin, expected_end))

    def test_yesterday(self):
        with self._patch_today():
            begin, end = MacroParser.parse_date_macro("@yesterday")
        yesterday = self.FIXED_TODAY - timedelta(days=1)
        expected_begin = to_ms(yesterday)
        expected_end = to_ms(self._end_of_day(yesterday))
        self.assertEqual((begin, end), (expected_begin, expected_end))

    def test_invalid_macro_behaves_like_today(self):
        with self._patch_today():
            try:
                begin_invalid, end_invalid = MacroParser.parse_date_macro("@notamacro")
            except SapioException:
                begin_invalid, end_invalid = MacroParser.parse_date_macro("@today")
            begin_today, end_today = MacroParser.parse_date_macro("@today")
        self.assertEqual((begin_invalid, end_invalid), (begin_today, end_today))

    # ------------------------------
    # Week macro (Sunday -> Saturday inclusive)
    # ------------------------------

    def test_thisweek(self):
        # FIXED_TODAY = Friday, 2025-02-14
        # Week is Sunday 2025-02-09 -> Saturday 2025-02-15
        with self._patch_today():
            begin, end = MacroParser.parse_date_macro("@thisweek")

        sunday = dt_utc(2025, 2, 9)
        saturday = dt_utc(2025, 2, 15)
        expected_begin = to_ms(sunday)
        expected_end = to_ms(self._end_of_day(saturday))
        self.assertEqual((begin, end), (expected_begin, expected_end))

    # ------------------------------
    # Month macros (1st -> last day inclusive)
    # ------------------------------

    def test_thismonth(self):
        # February 2025: 1 -> 28
        with self._patch_today():
            begin, end = MacroParser.parse_date_macro("@thismonth")

        first = dt_utc(2025, 2, 1)
        last = dt_utc(2025, 2, 28)
        self.assertEqual(begin, to_ms(first))
        self.assertEqual(end, to_ms(self._end_of_day(last)))

    def test_lastmonth(self):
        # January 2025: 1 -> 31
        with self._patch_today():
            begin, end = MacroParser.parse_date_macro("@lastmonth")

        first = dt_utc(2025, 1, 1)
        last = dt_utc(2025, 1, 31)
        self.assertEqual(begin, to_ms(first))
        self.assertEqual(end, to_ms(self._end_of_day(last)))

    def test_nextmonth(self):
        # March 2025: 1 -> 31
        with self._patch_today():
            begin, end = MacroParser.parse_date_macro("@nextmonth")

        first = dt_utc(2025, 3, 1)
        last = dt_utc(2025, 3, 31)
        self.assertEqual(begin, to_ms(first))
        self.assertEqual(end, to_ms(self._end_of_day(last)))

    # 12 @month<name> macros (all in 2025 for this fixed "today")

    def test_month_january(self):
        with self._patch_today():
            begin, end = MacroParser.parse_date_macro("@monthjanuary")
        first = dt_utc(2025, 1, 1)
        last = dt_utc(2025, 1, 31)
        self.assertEqual(begin, to_ms(first))
        self.assertEqual(end, to_ms(self._end_of_day(last)))

    def test_month_february(self):
        with self._patch_today():
            begin, end = MacroParser.parse_date_macro("@monthfebruary")
        first = dt_utc(2025, 2, 1)
        last = dt_utc(2025, 2, 28)  # 2025 not leap
        self.assertEqual(begin, to_ms(first))
        self.assertEqual(end, to_ms(self._end_of_day(last)))

    def test_month_march(self):
        with self._patch_today():
            begin, end = MacroParser.parse_date_macro("@monthmarch")
        first = dt_utc(2025, 3, 1)
        last = dt_utc(2025, 3, 31)
        self.assertEqual(begin, to_ms(first))
        self.assertEqual(end, to_ms(self._end_of_day(last)))

    def test_month_april(self):
        with self._patch_today():
            begin, end = MacroParser.parse_date_macro("@monthapril")
        first = dt_utc(2025, 4, 1)
        last = dt_utc(2025, 4, 30)
        self.assertEqual(begin, to_ms(first))
        self.assertEqual(end, to_ms(self._end_of_day(last)))

    def test_month_may(self):
        with self._patch_today():
            begin, end = MacroParser.parse_date_macro("@monthmay")
        first = dt_utc(2025, 5, 1)
        last = dt_utc(2025, 5, 31)
        self.assertEqual(begin, to_ms(first))
        self.assertEqual(end, to_ms(self._end_of_day(last)))

    def test_month_june(self):
        with self._patch_today():
            begin, end = MacroParser.parse_date_macro("@monthjune")
        first = dt_utc(2025, 6, 1)
        last = dt_utc(2025, 6, 30)
        self.assertEqual(begin, to_ms(first))
        self.assertEqual(end, to_ms(self._end_of_day(last)))

    def test_month_july(self):
        with self._patch_today():
            begin, end = MacroParser.parse_date_macro("@monthjuly")
        first = dt_utc(2025, 7, 1)
        last = dt_utc(2025, 7, 31)
        self.assertEqual(begin, to_ms(first))
        self.assertEqual(end, to_ms(self._end_of_day(last)))

    def test_month_august(self):
        with self._patch_today():
            begin, end = MacroParser.parse_date_macro("@monthaugust")
        first = dt_utc(2025, 8, 1)
        last = dt_utc(2025, 8, 31)
        self.assertEqual(begin, to_ms(first))
        self.assertEqual(end, to_ms(self._end_of_day(last)))

    def test_month_september(self):
        with self._patch_today():
            begin, end = MacroParser.parse_date_macro("@monthseptember")
        first = dt_utc(2025, 9, 1)
        last = dt_utc(2025, 9, 30)
        self.assertEqual(begin, to_ms(first))
        self.assertEqual(end, to_ms(self._end_of_day(last)))

    def test_month_october(self):
        with self._patch_today():
            begin, end = MacroParser.parse_date_macro("@monthoctober")
        first = dt_utc(2025, 10, 1)
        last = dt_utc(2025, 10, 31)
        self.assertEqual(begin, to_ms(first))
        self.assertEqual(end, to_ms(self._end_of_day(last)))

    def test_month_november(self):
        with self._patch_today():
            begin, end = MacroParser.parse_date_macro("@monthnovember")
        first = dt_utc(2025, 11, 1)
        last = dt_utc(2025, 11, 30)
        self.assertEqual(begin, to_ms(first))
        self.assertEqual(end, to_ms(self._end_of_day(last)))

    def test_month_december(self):
        with self._patch_today():
            begin, end = MacroParser.parse_date_macro("@monthdecember")
        first = dt_utc(2025, 12, 1)
        last = dt_utc(2025, 12, 31)
        self.assertEqual(begin, to_ms(first))
        self.assertEqual(end, to_ms(self._end_of_day(last)))

    # ------------------------------
    # Year macros
    # ------------------------------

    def test_thisyear(self):
        with self._patch_today():
            begin, end = MacroParser.parse_date_macro("@thisyear")
        first = dt_utc(2025, 1, 1)
        last = dt_utc(2025, 12, 31)
        self.assertEqual(begin, to_ms(first))
        self.assertEqual(end, to_ms(self._end_of_day(last)))

    def test_lastyear(self):
        with self._patch_today():
            begin, end = MacroParser.parse_date_macro("@lastyear")
        first = dt_utc(2024, 1, 1)
        last = dt_utc(2024, 12, 31)
        self.assertEqual(begin, to_ms(first))
        self.assertEqual(end, to_ms(self._end_of_day(last)))

    def test_nextyear(self):
        with self._patch_today():
            begin, end = MacroParser.parse_date_macro("@nextyear")
        first = dt_utc(2026, 1, 1)
        last = dt_utc(2026, 12, 31)
        self.assertEqual(begin, to_ms(first))
        self.assertEqual(end, to_ms(self._end_of_day(last)))

    # ------------------------------
    # last/next N days (example N=7)
    # ------------------------------

    def test_last7days(self):
        with self._patch_today():
            begin, end = MacroParser.parse_date_macro("@last7days")
        # last7days: [today-7, today] inclusive
        start = self.FIXED_TODAY - timedelta(days=7)
        end_dt = self.FIXED_TODAY
        self.assertEqual(begin, to_ms(start))
        self.assertEqual(end, to_ms(self._end_of_day(end_dt)))

    def test_next7days(self):
        with self._patch_today():
            begin, end = MacroParser.parse_date_macro("@next7days")
        # next7days: [today, today+7] inclusive
        start = self.FIXED_TODAY
        end_dt = self.FIXED_TODAY + timedelta(days=7)
        self.assertEqual(begin, to_ms(start))
        self.assertEqual(end, to_ms(self._end_of_day(end_dt)))


if __name__ == "__main__":
    unittest.main()
