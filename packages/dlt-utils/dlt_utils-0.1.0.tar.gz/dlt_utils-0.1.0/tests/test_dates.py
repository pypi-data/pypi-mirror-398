"""Tests for date utility functions."""

import pytest
from datetime import date
from dlt_utils import generate_year_weeks, generate_year_months
from dlt_utils.dates import get_current_iso_week, get_current_year_month


class TestGenerateYearWeeks:
    """Test suite for generate_year_weeks."""

    def test_specific_range(self):
        """Should generate correct weeks for a specific range."""
        result = generate_year_weeks(2024, 1, 2024, 4)
        
        assert result == [(2024, 1), (2024, 2), (2024, 3), (2024, 4)]

    def test_cross_year_boundary(self):
        """Should handle crossing year boundaries."""
        result = generate_year_weeks(2023, 51, 2024, 2)
        
        assert result == [(2023, 51), (2023, 52), (2024, 1), (2024, 2)]

    def test_single_week(self):
        """Should handle single week range."""
        result = generate_year_weeks(2024, 10, 2024, 10)
        
        assert result == [(2024, 10)]

    def test_default_start_year_uses_years_back(self):
        """Default start should be years_back years ago."""
        result = generate_year_weeks(
            start_week=1, 
            end_year=date.today().year - 2, 
            end_week=1,
            years_back=3
        )
        
        expected_start_year = date.today().year - 3
        assert result[0][0] == expected_start_year

    def test_custom_years_back(self):
        """Should respect custom years_back parameter."""
        result = generate_year_weeks(
            start_week=1,
            end_year=date.today().year - 1,
            end_week=1,
            years_back=1
        )
        
        expected_start_year = date.today().year - 1
        assert result[0][0] == expected_start_year

    def test_returns_list_of_tuples(self):
        """Should return a list of (year, week) tuples."""
        result = generate_year_weeks(2024, 1, 2024, 2)
        
        assert isinstance(result, list)
        assert all(isinstance(item, tuple) for item in result)
        assert all(len(item) == 2 for item in result)

    def test_chronological_order(self):
        """Weeks should be in chronological order."""
        result = generate_year_weeks(2023, 50, 2024, 5)
        
        for i in range(len(result) - 1):
            current = result[i]
            next_item = result[i + 1]
            # Either year increases or week increases within same year
            assert (current[0] < next_item[0]) or (
                current[0] == next_item[0] and current[1] < next_item[1]
            )


class TestGenerateYearMonths:
    """Test suite for generate_year_months."""

    def test_specific_range(self):
        """Should generate correct months for a specific range."""
        result = generate_year_months(2024, 10, 2025, 2)
        
        assert result == [
            (2024, 10), (2024, 11), (2024, 12),
            (2025, 1), (2025, 2)
        ]

    def test_single_month(self):
        """Should handle single month range."""
        result = generate_year_months(2024, 6, 2024, 6)
        
        assert result == [(2024, 6)]

    def test_full_year(self):
        """Should handle full year range."""
        result = generate_year_months(2024, 1, 2024, 12)
        
        assert len(result) == 12
        assert result[0] == (2024, 1)
        assert result[-1] == (2024, 12)

    def test_cross_year_boundary(self):
        """Should handle crossing year boundaries."""
        result = generate_year_months(2023, 11, 2024, 2)
        
        assert result == [(2023, 11), (2023, 12), (2024, 1), (2024, 2)]

    def test_default_start_year_uses_years_back(self):
        """Default start should be years_back years ago."""
        result = generate_year_months(
            start_month=1,
            end_year=date.today().year - 2,
            end_month=1,
            years_back=3
        )
        
        expected_start_year = date.today().year - 3
        assert result[0][0] == expected_start_year

    def test_returns_list_of_tuples(self):
        """Should return a list of (year, month) tuples."""
        result = generate_year_months(2024, 1, 2024, 3)
        
        assert isinstance(result, list)
        assert all(isinstance(item, tuple) for item in result)
        assert all(len(item) == 2 for item in result)

    def test_months_are_valid(self):
        """All months should be between 1 and 12."""
        result = generate_year_months(2023, 1, 2025, 12)
        
        for year, month in result:
            assert 1 <= month <= 12


class TestCurrentDateHelpers:
    """Test suite for current date helper functions."""

    def test_get_current_iso_week_returns_tuple(self):
        """Should return a (year, week) tuple."""
        result = get_current_iso_week()
        
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], int)
        assert isinstance(result[1], int)

    def test_get_current_iso_week_valid_range(self):
        """Week should be between 1 and 53."""
        year, week = get_current_iso_week()
        
        assert 1 <= week <= 53
        assert year >= 2020  # Sanity check

    def test_get_current_year_month_returns_tuple(self):
        """Should return a (year, month) tuple."""
        result = get_current_year_month()
        
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], int)
        assert isinstance(result[1], int)

    def test_get_current_year_month_valid_range(self):
        """Month should be between 1 and 12."""
        year, month = get_current_year_month()
        
        assert 1 <= month <= 12
        assert year >= 2020  # Sanity check
