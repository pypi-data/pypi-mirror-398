"""
MockContext provides a test implementation of the Context interface.

It stores message data in memory using JSON for testing nodes without the full runtime.
"""

import json
import uuid
import threading
from typing import Any, Dict, Optional


class MockContext:
    """
    MockContext implements the Context interface for testing purposes.
    It stores values in memory without requiring the full Robomotion runtime.
    """

    def __init__(self, initial_data: Optional[Dict[str, Any]] = None):
        """
        Create a new MockContext with optional initial data.

        Args:
            initial_data: Optional dictionary to initialize the context with
        """
        self._lock = threading.RLock()
        self._data: Dict[str, Any] = {}
        self._id = str(uuid.uuid4())

        if initial_data is not None:
            self._data = dict(initial_data)
            if 'id' in initial_data:
                self._id = str(initial_data['id'])

    @classmethod
    def from_json(cls, json_data: bytes) -> 'MockContext':
        """
        Create a MockContext from JSON bytes.

        Args:
            json_data: JSON bytes to parse

        Returns:
            New MockContext instance
        """
        ctx = cls()
        if json_data:
            data = json.loads(json_data.decode('utf-8'))
            ctx._data = data
            if 'id' in data:
                ctx._id = str(data['id'])
        return ctx

    def get_id(self) -> str:
        """Return the message ID."""
        return self._id

    def set(self, key: str, value: Any) -> None:
        """
        Set a value at the given path.

        Args:
            key: The path/key to set (e.g., "user.name" or "items[0].value")
            value: The value to set
        """
        with self._lock:
            self._set_at_path(key, value)

    def get(self, key: str) -> Any:
        """
        Get a value from the given path.

        Args:
            key: The path/key to get

        Returns:
            The value at the path, or None if not found
        """
        with self._lock:
            return self._get_at_path(key)

    def get_string(self, key: str) -> str:
        """
        Get a string value from the specified path.

        Args:
            key: The path/key to get

        Returns:
            The value as a string, or empty string if not found
        """
        val = self.get(key)
        if val is None:
            return ""
        return str(val)

    def get_bool(self, key: str) -> bool:
        """
        Get a boolean value from the specified path.

        Args:
            key: The path/key to get

        Returns:
            The value as a boolean
        """
        val = self.get(key)
        if val is None:
            return False
        if isinstance(val, bool):
            return val
        if isinstance(val, (int, float)):
            return val > 0
        if isinstance(val, str):
            return val.lower() in ('true', '1', 'yes')
        return bool(val)

    def get_int(self, key: str) -> int:
        """
        Get an integer value from the specified path.

        Args:
            key: The path/key to get

        Returns:
            The value as an integer, or 0 if not found
        """
        val = self.get(key)
        if val is None:
            return 0
        if isinstance(val, (int, float)):
            return int(val)
        if isinstance(val, str):
            try:
                return int(val)
            except ValueError:
                return 0
        return 0

    def get_float(self, key: str) -> float:
        """
        Get a float value from the specified path.

        Args:
            key: The path/key to get

        Returns:
            The value as a float, or 0.0 if not found
        """
        val = self.get(key)
        if val is None:
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            try:
                return float(val)
            except ValueError:
                return 0.0
        return 0.0

    def get_raw(self) -> bytes:
        """
        Get the raw JSON bytes of the context.

        Returns:
            JSON bytes
        """
        with self._lock:
            return json.dumps(self._data).encode('utf-8')

    def set_raw(self, data: bytes) -> None:
        """
        Set the raw JSON bytes of the context.

        Args:
            data: JSON bytes to set
        """
        with self._lock:
            if data:
                self._data = json.loads(data.decode('utf-8'))
            else:
                self._data = {}

    def is_empty(self) -> bool:
        """
        Check if the context is empty.

        Returns:
            True if empty, False otherwise
        """
        with self._lock:
            return len(self._data) == 0

    def get_all(self) -> Dict[str, Any]:
        """
        Get all data as a dictionary.

        Returns:
            Copy of all data
        """
        with self._lock:
            return dict(self._data)

    def to_json(self) -> str:
        """
        Get the current state as a JSON string.

        Returns:
            JSON string
        """
        with self._lock:
            return json.dumps(self._data, indent=2)

    def clear(self) -> None:
        """Clear all data from the context."""
        with self._lock:
            self._data = {}

    def clone(self) -> 'MockContext':
        """
        Create and return a new MockContext with the same data.

        Returns:
            New MockContext instance with copied data
        """
        with self._lock:
            new_ctx = MockContext(dict(self._data))
            new_ctx._id = self._id
            return new_ctx

    def delete(self, key: str) -> None:
        """
        Delete a value at the given path.

        Args:
            key: The path/key to delete
        """
        with self._lock:
            if key in self._data:
                del self._data[key]

    def _set_at_path(self, path: str, value: Any) -> None:
        """Set a value at a nested path, creating intermediate objects as needed."""
        parts = self._parse_path(path)
        if not parts:
            return

        current = self._data
        for i, part in enumerate(parts[:-1]):
            next_part = parts[i + 1]

            if part['is_index']:
                # Ensure current is a list
                if not isinstance(current, list):
                    return
                while len(current) <= part['index']:
                    if next_part['is_index']:
                        current.append([])
                    else:
                        current.append({})
                current = current[part['index']]
            else:
                # Ensure current is a dict
                if not isinstance(current, dict):
                    return
                if part['name'] not in current:
                    if next_part['is_index']:
                        current[part['name']] = []
                    else:
                        current[part['name']] = {}
                current = current[part['name']]

        # Set the final value
        last_part = parts[-1]
        if last_part['is_index']:
            if isinstance(current, list):
                while len(current) <= last_part['index']:
                    current.append(None)
                current[last_part['index']] = value
        else:
            if isinstance(current, dict):
                current[last_part['name']] = value

    def _get_at_path(self, path: str) -> Any:
        """Get a value at a nested path."""
        parts = self._parse_path(path)
        if not parts:
            return self._data

        current = self._data
        for part in parts:
            if current is None:
                return None

            if part['is_index']:
                if isinstance(current, list) and part['index'] < len(current):
                    current = current[part['index']]
                else:
                    return None
            else:
                if isinstance(current, dict) and part['name'] in current:
                    current = current[part['name']]
                else:
                    return None

        return current

    def _parse_path(self, path: str) -> list:
        """Parse a JSON path into segments."""
        result = []
        current = []
        in_bracket = False

        for char in path:
            if char == '.':
                if current:
                    result.append({'is_index': False, 'name': ''.join(current)})
                    current = []
            elif char == '[':
                if current:
                    result.append({'is_index': False, 'name': ''.join(current)})
                    current = []
                in_bracket = True
            elif char == ']':
                if in_bracket and current:
                    index_str = ''.join(current)
                    try:
                        result.append({'is_index': True, 'index': int(index_str)})
                    except ValueError:
                        # Treat as property name
                        result.append({'is_index': False, 'name': index_str})
                    current = []
                in_bracket = False
            else:
                current.append(char)

        if current:
            result.append({'is_index': False, 'name': ''.join(current)})

        return result
