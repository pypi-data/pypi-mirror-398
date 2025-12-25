from dataclasses import fields
from typing import Any, TypeVar

from prestashop_webservice.client import Client
from prestashop_webservice.params import Params

T = TypeVar("T")


class BaseModel:
    """Base class for model queries with automatic dataclass conversion."""

    _data_class: type[Any] | None = None
    _MAX_FILTER_BYTES = 1500

    def __init__(self, client: Client):
        self.client = client

    @staticmethod
    def _to_list(result: dict | list) -> list[dict]:
        """Ensure result is always a list.

        Args:
            result: Result from API call (dict or list)

        Returns:
            List of dictionaries
        """
        if isinstance(result, dict):
            return [result] if result else []
        return result or []

    def _query(self, endpoint: str, params: Params | None = None, response_key: str = "") -> Any:
        """Override Client._query to return dataclass instances instead of dicts.

        Args:
            endpoint: API endpoint to query
            params: Query parameters
            response_key: Key to extract from JSON response

        Returns:
            Single dataclass instance or list of dataclass instances
        """

        if params and params.filter:
            filter_str = str(params.filter)
            if len(filter_str.encode("utf-8")) > self._MAX_FILTER_BYTES:
                filter_chunks = self._split_filter(params)
                merged_results: list[dict] = []
                for chunk in filter_chunks:
                    if not chunk:
                        continue
                    chunk_params = Params(
                        filter=chunk,
                        display=params.display,
                        limit=params.limit,
                        sort=params.sort,
                        date=params.date,
                    )
                    partial = self.client._query(endpoint, chunk_params, response_key)
                    merged_results.extend(self._to_list(partial))

                result = merged_results
            else:
                result = self.client._query(endpoint, params, response_key)
        else:
            result = self.client._query(endpoint, params, response_key)

        # If no data_class is set, return raw result
        if self._data_class is None:
            return result

        # Convert to list and instantiate dataclasses
        results = self._to_list(result)
        instances = []
        for r in results:
            # Filter out unknown fields to avoid TypeError
            if self._data_class:
                field_names = {f.name for f in fields(self._data_class)}
                filtered = {k: v for k, v in r.items() if k in field_names}
                instances.append(self._data_class(**filtered))

        # Return single instance if result was dict, list if it was list
        if isinstance(result, dict):
            return instances[0] if instances else None
        return instances

    def _split_filter(self, params: Params) -> list[dict]:
        """Split a large filter payload into smaller chunks."""
        if not params.filter:
            return []

        # Multiple keys: split dict in half
        if len(params.filter) > 1:
            items = list(params.filter.items())
            mid_index = len(items) // 2
            return [dict(items[:mid_index]), dict(items[mid_index:])]

        # Single key with huge value: split the value into safe-size chunks
        key, value = next(iter(params.filter.items()))
        value_str = str(value)
        inner = (
            value_str[1:-1] if value_str.startswith("[") and value_str.endswith("]") else value_str
        )
        parts = inner.split("|") if "|" in inner else [inner]

        filter_chunks: list[dict] = []
        current: list[str] = []
        for part in parts:
            candidate = "|".join(current + [part]) if current else part
            encoded_len = len(f"[{candidate}]".encode())
            if encoded_len > self._MAX_FILTER_BYTES and current:
                filter_chunks.append({key: "|".join(current)})
                current = [part]
            else:
                current.append(part)

        if current:
            filter_chunks.append({key: "|".join(current)})

        return filter_chunks or [params.filter]
