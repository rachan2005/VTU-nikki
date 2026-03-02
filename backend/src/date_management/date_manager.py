"""Advanced date management with range support and smart filtering"""
from datetime import date, datetime, timedelta
from typing import List, Union, Optional
import re

try:
    from dateutil import parser as date_parser
    from dateutil.relativedelta import relativedelta
    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False

try:
    import holidays
    HOLIDAYS_AVAILABLE = True
except ImportError:
    HOLIDAYS_AVAILABLE = False

from config import DEFAULT_COUNTRY, SKIP_WEEKENDS, SKIP_HOLIDAYS, MAX_DATE_RANGE_DAYS
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DateManager:
    """Advanced date parsing and management"""

    def __init__(
        self,
        country: str = DEFAULT_COUNTRY,
        skip_weekends: bool = SKIP_WEEKENDS,
        skip_holidays: bool = SKIP_HOLIDAYS
    ):
        self.country = country
        self.skip_weekends = skip_weekends
        self.skip_holidays = skip_holidays
        self.current_date = date.today()

        # Load holiday calendar
        if HOLIDAYS_AVAILABLE and skip_holidays:
            self.holiday_calendar = holidays.country_holidays(country)
            logger.info(f"Loaded {country} holiday calendar")
        else:
            self.holiday_calendar = None

    def parse_date_input(
        self,
        date_input: Union[str, List[str], date],
        skip_weekends: Optional[bool] = None,
        skip_holidays: Optional[bool] = None
    ) -> List[date]:
        """
        Parse various date input formats.

        Supports:
        - Single date: "2025-01-15", "January 15, 2025", date object
        - Range: "2025-01-01 to 2025-01-31", "2025-01-01 - 2025-01-31"
        - Relative: "last week", "last month", "yesterday"
        - List: ["2025-01-10", "2025-01-15", "2025-01-20"]

        Returns:
            List of date objects (sorted, unique, filtered)
        """
        if not DATEUTIL_AVAILABLE:
            raise ImportError("dateutil required. Install with: pip install python-dateutil")

        # Use instance defaults if not specified
        skip_weekends = skip_weekends if skip_weekends is not None else self.skip_weekends
        skip_holidays = skip_holidays if skip_holidays is not None else self.skip_holidays

        # Handle date object
        if isinstance(date_input, date):
            return [date_input]

        # Handle list of dates
        if isinstance(date_input, list):
            dates = []
            for d in date_input:
                if isinstance(d, date):
                    dates.append(d)
                else:
                    parsed = self._parse_single_date(str(d))
                    if parsed:
                        dates.append(parsed)
            return self._filter_dates(sorted(set(dates)), skip_weekends, skip_holidays)

        # Parse string input
        date_input = str(date_input).strip()

        # Check for comma-separated dates (from calendar picker)
        if "," in date_input:
            date_strings = [d.strip() for d in date_input.split(",")]
            dates = []
            for d_str in date_strings:
                parsed = self._parse_single_date(d_str)
                if parsed:
                    dates.append(parsed)
            return self._filter_dates(sorted(set(dates)), skip_weekends, skip_holidays)

        # Check for range
        if " to " in date_input.lower() or " - " in date_input:
            return self._parse_range(date_input, skip_weekends, skip_holidays)

        # Check for relative dates
        if "last" in date_input.lower() or "yesterday" in date_input.lower():
            return self._parse_relative(date_input, skip_weekends, skip_holidays)

        # Single date
        parsed = self._parse_single_date(date_input)
        if parsed:
            return self._filter_dates([parsed], skip_weekends, skip_holidays)

        raise ValueError(f"Could not parse date input: {date_input}")

    def _parse_single_date(self, date_str: str) -> Optional[date]:
        """Parse single date string"""
        try:
            dt = date_parser.parse(date_str)
            return dt.date() if hasattr(dt, 'date') else dt
        except Exception as e:
            logger.warning(f"Failed to parse date '{date_str}': {e}")
            return None

    def _parse_range(
        self,
        range_str: str,
        skip_weekends: bool,
        skip_holidays: bool
    ) -> List[date]:
        """Parse date range string"""
        # Split on 'to' or '-'
        if " to " in range_str.lower():
            parts = range_str.lower().split(" to ")
        else:
            parts = range_str.split(" - ")

        if len(parts) != 2:
            raise ValueError(f"Invalid range format: {range_str}")

        start_date = self._parse_single_date(parts[0].strip())
        end_date = self._parse_single_date(parts[1].strip())

        if not start_date or not end_date:
            raise ValueError(f"Could not parse range: {range_str}")

        if start_date > end_date:
            start_date, end_date = end_date, start_date

        # Check max range
        days_diff = (end_date - start_date).days
        if days_diff > MAX_DATE_RANGE_DAYS:
            raise ValueError(
                f"Date range too large: {days_diff} days. "
                f"Maximum allowed: {MAX_DATE_RANGE_DAYS} days"
            )

        return self._generate_date_range(start_date, end_date, skip_weekends, skip_holidays)

    def _parse_relative(
        self,
        relative_str: str,
        skip_weekends: bool,
        skip_holidays: bool
    ) -> List[date]:
        """Parse relative date expressions"""
        relative_lower = relative_str.lower().strip()

        # Yesterday
        if "yesterday" in relative_lower:
            yesterday = self.current_date - timedelta(days=1)
            return self._filter_dates([yesterday], skip_weekends, skip_holidays)

        # Last week (previous Mon-Fri)
        if "last week" in relative_lower:
            # Find last Monday
            days_since_monday = (self.current_date.weekday() + 7) % 7
            last_monday = self.current_date - timedelta(days=days_since_monday + 7)
            last_friday = last_monday + timedelta(days=4)
            return self._generate_date_range(last_monday, last_friday, skip_weekends, skip_holidays)

        # Last month
        if "last month" in relative_lower:
            first_of_this_month = self.current_date.replace(day=1)
            first_of_last_month = first_of_this_month - relativedelta(months=1)
            last_of_last_month = first_of_this_month - timedelta(days=1)
            return self._generate_date_range(
                first_of_last_month,
                last_of_last_month,
                skip_weekends,
                skip_holidays
            )

        # This week
        if "this week" in relative_lower:
            days_since_monday = self.current_date.weekday()
            this_monday = self.current_date - timedelta(days=days_since_monday)
            return self._generate_date_range(this_monday, self.current_date, skip_weekends, skip_holidays)

        raise ValueError(f"Unknown relative date format: {relative_str}")

    def _generate_date_range(
        self,
        start: date,
        end: date,
        skip_weekends: bool,
        skip_holidays: bool
    ) -> List[date]:
        """Generate all dates in range with filters"""
        dates = []
        current = start

        while current <= end:
            # Check weekend
            if skip_weekends and current.weekday() >= 5:  # Saturday=5, Sunday=6
                current += timedelta(days=1)
                continue

            # Check holiday
            if skip_holidays and self.holiday_calendar and current in self.holiday_calendar:
                logger.debug(f"Skipping holiday: {current} ({self.holiday_calendar.get(current)})")
                current += timedelta(days=1)
                continue

            dates.append(current)
            current += timedelta(days=1)

        return dates

    def _filter_dates(
        self,
        dates: List[date],
        skip_weekends: bool,
        skip_holidays: bool
    ) -> List[date]:
        """Filter dates by weekend/holiday rules"""
        filtered = []

        for d in dates:
            # Skip weekends
            if skip_weekends and d.weekday() >= 5:
                continue

            # Skip holidays
            if skip_holidays and self.holiday_calendar and d in self.holiday_calendar:
                continue

            filtered.append(d)

        return filtered

    def is_working_day(self, check_date: date) -> bool:
        """Check if date is a working day (not weekend/holiday)"""
        # Weekend check
        if self.skip_weekends and check_date.weekday() >= 5:
            return False

        # Holiday check
        if self.skip_holidays and self.holiday_calendar:
            if check_date in self.holiday_calendar:
                return False

        return True

    def get_next_working_day(self, start_date: date) -> date:
        """Get next working day after given date"""
        current = start_date + timedelta(days=1)
        while not self.is_working_day(current):
            current += timedelta(days=1)
        return current

    def get_working_days_count(self, start: date, end: date) -> int:
        """Count working days in range"""
        dates = self._generate_date_range(start, end, self.skip_weekends, self.skip_holidays)
        return len(dates)
