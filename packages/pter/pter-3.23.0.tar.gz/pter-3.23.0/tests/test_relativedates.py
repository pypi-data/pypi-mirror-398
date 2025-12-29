import datetime
import unittest

from pter.utils import get_relative_date


class TestRelativeDates(unittest.TestCase):
    def test_simple_case(self):
        today = datetime.date(2024, 11, 7)
        assert today.isoweekday() == 4  # Thursday

        then = get_relative_date('+2d', base=today)
        expected = datetime.date(2024, 11, 9)

        self.assertEqual(then, expected)

    def test_business_day_avoidance(self):
        today = datetime.date(2024, 11, 7)
        assert today.isoweekday() == 4  # Thursday

        # saturday
        then = get_relative_date('+2b', base=today)
        expected = datetime.date(2024, 11, 11)

        self.assertEqual(then, expected)

        # sunday
        then = get_relative_date('+3b', base=today)
        self.assertEqual(then, expected)

        # monday
        then = get_relative_date('+4b', base=today)
        self.assertEqual(then, expected)

    def test_business_day_avoidance2(self):
        today = datetime.date(2024, 11, 7)
        assert today.isoweekday() == 4  # Thursday

        # saturday, but negative!
        then = get_relative_date('+3d-1b', base=today)
        expected = datetime.date(2024, 11, 8)

        self.assertEqual(then, expected)

    def test_documented_business_case(self):
        today = datetime.date(2024, 11, 6)
        assert today.isoweekday() == 3  # Wednesday

        # sunday, but negative!
        then = get_relative_date('+2w-4b', base=today)
        expected = datetime.date(2024, 11, 15)

        self.assertEqual(then, expected)
