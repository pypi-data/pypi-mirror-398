"""
Utility functions for date-based partitioning in dlt data extraction.

This module provides helper functions to generate sequences of (year, week) and
(year, month) tuples for partitioning data extraction across time periods.
These are used by resources that require parametric date-based queries.
"""

from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple


def generate_year_weeks(
    start_year: Optional[int] = None,
    start_week: Optional[int] = 1,
    end_year: Optional[int] = None,
    end_week: Optional[int] = None,
    years_back: int = 3,
    weeks_forward: int = 52,
) -> List[Tuple[int, int]]:
    """
    Generate a list of (year, week) tuples using ISO week numbers.

    Uses ISO 8601 week numbers where weeks start on Monday and the first
    week of the year contains at least 4 days in that year.

    Args:
        start_year: Start year. Defaults to `years_back` years ago.
        start_week: Start ISO week number 1-53. Defaults to 1.
        end_year: End year. Defaults to the year of calculated end date.
        end_week: End ISO week number 1-53. Defaults to current + `weeks_forward`.
        years_back: Years to go back for default start_year. Defaults to 3.
        weeks_forward: Weeks to add for default end calculation. Defaults to 52.

    Returns:
        List of (year, week) tuples in chronological order.

    Examples:
        >>> # Specific range
        >>> generate_year_weeks(2024, 1, 2024, 4)
        [(2024, 1), (2024, 2), (2024, 3), (2024, 4)]

        >>> # Default: 3 years back to 52 weeks forward
        >>> weeks = generate_year_weeks()
        >>> weeks[0]  # First week
        (2022, 1)

        >>> # Custom defaults
        >>> generate_year_weeks(years_back=1, weeks_forward=4)
        # From 1 year ago to 4 weeks from now
    """
    today = date.today()

    # Default start_year: years_back years ago
    if start_year is None:
        start_year = today.year - years_back

    # Default end: current date + weeks_forward
    if end_year is None or end_week is None:
        future_date = today + timedelta(weeks=weeks_forward)
        iso_cal = future_date.isocalendar()
        end_year = end_year or iso_cal.year
        end_week = end_week or iso_cal.week

    # Start from start_week of start_year
    start_date = datetime.strptime(f"{start_year}-W{start_week:02d}-1", "%G-W%V-%u").date()
    end_date = datetime.strptime(f"{end_year}-W{end_week:02d}-1", "%G-W%V-%u").date()

    year_weeks = []
    current = start_date
    while current <= end_date:
        iso_cal = current.isocalendar()
        year_weeks.append((iso_cal.year, iso_cal.week))
        current += timedelta(weeks=1)

    return year_weeks


def generate_year_months(
    start_year: Optional[int] = None,
    start_month: Optional[int] = 1,
    end_year: Optional[int] = None,
    end_month: Optional[int] = None,
    years_back: int = 3,
    months_forward: int = 1,
) -> List[Tuple[int, int]]:
    """
    Generate a list of (year, month) tuples from start to end.

    Args:
        start_year: Start year. Defaults to `years_back` years ago.
        start_month: Start month 1-12. Defaults to 1 (January).
        end_year: End year. Defaults to the year of calculated end date.
        end_month: End month 1-12. Defaults to current + `months_forward`.
        years_back: Years to go back for default start_year. Defaults to 3.
        months_forward: Months to add for default end calculation. Defaults to 1.

    Returns:
        List of (year, month) tuples in chronological order.

    Examples:
        >>> generate_year_months(2024, 10, 2025, 2)
        [(2024, 10), (2024, 11), (2024, 12), (2025, 1), (2025, 2)]

        >>> # Default: 3 years back to 1 month forward
        >>> months = generate_year_months()
        >>> months[0]
        (2022, 1)
    """
    today = date.today()

    # Default start_year: years_back years ago
    if start_year is None:
        start_year = today.year - years_back

    # Default end: current date + months_forward
    if end_year is None or end_month is None:
        # Calculate future date by adding months
        future_month = today.month + months_forward
        future_year = today.year
        while future_month > 12:
            future_month -= 12
            future_year += 1
        end_year = end_year or future_year
        end_month = end_month or future_month

    year_months = []
    current_year = start_year
    current_month = start_month

    while (current_year, current_month) <= (end_year, end_month):
        year_months.append((current_year, current_month))
        current_month += 1
        if current_month > 12:
            current_month = 1
            current_year += 1

    return year_months


def get_current_iso_week() -> Tuple[int, int]:
    """
    Get the current ISO year and week number.

    Returns:
        Tuple of (year, week) for today.
    """
    iso_cal = date.today().isocalendar()
    return (iso_cal.year, iso_cal.week)


def get_current_year_month() -> Tuple[int, int]:
    """
    Get the current year and month.

    Returns:
        Tuple of (year, month) for today.
    """
    today = date.today()
    return (today.year, today.month)
