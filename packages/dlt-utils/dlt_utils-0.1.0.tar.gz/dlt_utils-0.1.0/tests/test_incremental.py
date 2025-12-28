"""Tests for PartitionedIncremental class."""

import pytest
from dlt_utils import PartitionedIncremental


class TestPartitionedIncremental:
    """Test suite for PartitionedIncremental."""

    def test_initial_value_returned_for_new_partition(self):
        """New partitions should return the initial_value."""
        state = {}
        inc = PartitionedIncremental(
            state=state,
            state_key="sequences",
            initial_value=0,
        )

        assert inc.get_last_value("company_a") == 0
        assert inc.get_last_value("company_b") == 0

    def test_none_returned_when_no_initial_value(self):
        """When no initial_value is set, None should be returned."""
        state = {}
        inc = PartitionedIncremental(
            state=state,
            state_key="sequences",
        )

        assert inc.get_last_value("company_a") is None

    def test_track_updates_state(self):
        """Tracking a value should update the state."""
        state = {}
        inc = PartitionedIncremental(
            state=state,
            state_key="sequences",
            initial_value=0,
        )

        inc.track("company_a", 100)
        assert state["sequences"]["company_a"] == 100

        inc.track("company_a", 200)
        assert state["sequences"]["company_a"] == 200

    def test_track_keeps_max_by_default(self):
        """By default, track should keep the maximum value."""
        state = {}
        inc = PartitionedIncremental(
            state=state,
            state_key="sequences",
            initial_value=0,
        )

        inc.track("company_a", 100)
        inc.track("company_a", 50)  # Lower value
        inc.track("company_a", 150)

        assert state["sequences"]["company_a"] == 150

    def test_track_with_min_function(self):
        """With min as last_value_func, track should keep the minimum."""
        state = {}
        inc = PartitionedIncremental(
            state=state,
            state_key="sequences",
            initial_value=1000,
            last_value_func=min,
        )

        inc.track("company_a", 100)
        inc.track("company_a", 50)
        inc.track("company_a", 150)

        assert state["sequences"]["company_a"] == 50

    def test_partitions_are_independent(self):
        """Each partition should have its own state."""
        state = {}
        inc = PartitionedIncremental(
            state=state,
            state_key="sequences",
            initial_value=0,
        )

        inc.track("company_a", 100)
        inc.track("company_b", 200)
        inc.track("company_c", 300)

        assert state["sequences"]["company_a"] == 100
        assert state["sequences"]["company_b"] == 200
        assert state["sequences"]["company_c"] == 300

    def test_get_last_value_after_track(self):
        """get_last_value should return the tracked value."""
        state = {}
        inc = PartitionedIncremental(
            state=state,
            state_key="sequences",
            initial_value=0,
        )

        inc.track("company_a", 100)
        assert inc.get_last_value("company_a") == 100

    def test_existing_state_is_preserved(self):
        """Existing state should be loaded and preserved."""
        state = {"sequences": {"company_a": 500}}
        inc = PartitionedIncremental(
            state=state,
            state_key="sequences",
            initial_value=0,
        )

        assert inc.get_last_value("company_a") == 500
        assert inc.get_last_value("company_b") == 0  # New partition

    def test_track_record_extracts_cursor(self):
        """track_record should extract cursor from record."""
        state = {}
        inc = PartitionedIncremental(
            state=state,
            state_key="sequences",
            cursor_path="sequenceNumber",
            initial_value=0,
        )

        record = {"id": "123", "sequenceNumber": 100, "name": "Test"}
        result = inc.track_record("company_a", record)

        assert result is record  # Returns same record
        assert state["sequences"]["company_a"] == 100

    def test_track_record_returns_record_unchanged(self):
        """track_record should return the record unchanged for chaining."""
        state = {}
        inc = PartitionedIncremental(
            state=state,
            state_key="sequences",
            cursor_path="seq",
            initial_value=0,
        )

        original = {"seq": 42, "data": "test"}
        result = inc.track_record("company_a", original)

        assert result == original
        assert result is original

    def test_track_ignores_none_values(self):
        """Tracking None should not update state."""
        state = {}
        inc = PartitionedIncremental(
            state=state,
            state_key="sequences",
            initial_value=0,
        )

        inc.track("company_a", 100)
        inc.track("company_a", None)

        assert state["sequences"]["company_a"] == 100

    def test_get_all_partitions(self):
        """get_all_partitions should return all tracked partitions."""
        state = {}
        inc = PartitionedIncremental(
            state=state,
            state_key="sequences",
            initial_value=0,
        )

        inc.track("company_a", 100)
        inc.track("company_b", 200)

        partitions = inc.get_all_partitions()
        assert partitions == {"company_a": 100, "company_b": 200}

    def test_reset_partition(self):
        """reset_partition should remove state for a partition."""
        state = {}
        inc = PartitionedIncremental(
            state=state,
            state_key="sequences",
            initial_value=0,
        )

        inc.track("company_a", 100)
        inc.track("company_b", 200)
        inc.reset_partition("company_a")

        assert "company_a" not in state["sequences"]
        assert state["sequences"]["company_b"] == 200
        assert inc.get_last_value("company_a") == 0  # Returns initial_value

    def test_datetime_cursor_with_max(self):
        """Should work with datetime strings as cursors."""
        state = {}
        inc = PartitionedIncremental(
            state=state,
            state_key="last_modified",
            initial_value="2020-01-01T00:00:00",
        )

        inc.track("company_a", "2024-01-15T10:30:00")
        inc.track("company_a", "2024-01-10T08:00:00")  # Earlier
        inc.track("company_a", "2024-01-20T14:45:00")  # Latest

        assert state["last_modified"]["company_a"] == "2024-01-20T14:45:00"
