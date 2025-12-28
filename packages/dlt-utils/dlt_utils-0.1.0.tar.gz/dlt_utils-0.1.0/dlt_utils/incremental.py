"""
Incremental state tracking voor dlt resources met partitionering.

Dit module biedt een PartitionedIncremental class die werkt als dlt.sources.incremental,
maar state per partition key (bijv. company_id) bijhoudt in plaats van per resource.
"""

from typing import Any, Callable, Dict, List, TypeVar

TCursorValue = TypeVar("TCursorValue")


class PartitionedIncremental:
    """
    Incremental state tracking per partition key (bijv. company_id).

    Werkt als dlt.sources.incremental, maar partitioneert state per key zodat
    meerdere companies onafhankelijke cursors kunnen hebben binnen dezelfde resource.

    Voorbeeld:
        ```python
        @dlt.resource
        def sync_resource():
            state = dlt.current.resource_state()
            inc = PartitionedIncremental(
                state=state,
                state_key="sequences",
                cursor_path="sequenceNumber",
                initial_value=0,
            )

            for company_id in ["company_a", "company_b"]:
                start_seq = inc.get_last_value(company_id)
                for record in fetch_data(company_id, since=start_seq):
                    inc.track(company_id, record["sequenceNumber"])
                    yield record
        ```

    State structuur in dlt:
        ```json
        {
            "sequences": {
                "company_a": 12345,
                "company_b": 67890
            }
        }
        ```

    Use cases:
        - sequenceNumber tracking per company (Floriday sync endpoints)
        - last_modified_at per company + period (Easyflex journaalposten)
        - Any cursor that needs to be tracked per partition
    """

    def __init__(
        self,
        state: Dict[str, Any],
        state_key: str,
        cursor_path: str = None,
        initial_value: TCursorValue = None,
        last_value_func: Callable[[List[TCursorValue]], TCursorValue] = max,
    ):
        """
        Initialiseer PartitionedIncremental.

        Args:
            state: Resource state dict van dlt.current.resource_state().
            state_key: Sleutel in state dict waar partition values worden opgeslagen.
            cursor_path: Optioneel pad naar cursor veld in records (voor track_record).
            initial_value: Waarde voor partitions zonder bestaande state.
            last_value_func: Functie om "laatste" waarde te bepalen (default: max).
                             Gebruik min() voor aflopende cursors.
        """
        self._state = state
        self._state_key = state_key
        self._cursor_path = cursor_path
        self._initial_value = initial_value
        self._last_value_func = last_value_func

        # Zorg dat state structuur bestaat
        if state_key not in state:
            state[state_key] = {}
        self._partition_state = state[state_key]

        # Track huidige waarden tijdens streaming (voor running max/min)
        self._current_values: Dict[str, TCursorValue] = {}

    def get_last_value(self, partition_key: str) -> TCursorValue:
        """
        Haal de laatst opgeslagen waarde op voor een partition.

        Args:
            partition_key: Identifier voor de partition (bijv. company_id).

        Returns:
            De opgeslagen waarde, of initial_value als er geen state is.
        """
        return self._partition_state.get(partition_key, self._initial_value)

    def track(self, partition_key: str, cursor_value: TCursorValue) -> None:
        """
        Track een cursor waarde voor een partition.

        Werkt running max/min bij en persisted naar state. Roep dit aan voor
        elk record tijdens het streamen zodat de hoogste/laagste waarde
        wordt onthouden.

        Args:
            partition_key: Identifier voor de partition (bijv. company_id).
            cursor_value: De te tracken waarde (bijv. sequenceNumber).
        """
        current = self._current_values.get(partition_key)
        if current is None:
            current = self.get_last_value(partition_key)

        if cursor_value is not None:
            new_value = self._last_value_func(
                [cursor_value, current] if current is not None else [cursor_value]
            )
            self._current_values[partition_key] = new_value
            # Direct persisten naar state (dlt commit na resource completion)
            self._partition_state[partition_key] = new_value

    def track_record(self, partition_key: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track cursor waarde uit een record via cursor_path.

        Convenience methode voor gebruik in map functies.

        Args:
            partition_key: Identifier voor de partition.
            record: Record dict met cursor veld.

        Returns:
            Het record ongewijzigd (voor chaining in pipelines).
        """
        if self._cursor_path:
            cursor_value = record.get(self._cursor_path)
            self.track(partition_key, cursor_value)
        return record

    def get_all_partitions(self) -> Dict[str, TCursorValue]:
        """
        Haal alle opgeslagen partition states op.

        Returns:
            Dict van partition_key -> cursor_value.
        """
        return dict(self._partition_state)

    def reset_partition(self, partition_key: str) -> None:
        """
        Reset state voor een specifieke partition.

        Args:
            partition_key: Identifier voor de partition om te resetten.
        """
        if partition_key in self._partition_state:
            del self._partition_state[partition_key]
        if partition_key in self._current_values:
            del self._current_values[partition_key]
