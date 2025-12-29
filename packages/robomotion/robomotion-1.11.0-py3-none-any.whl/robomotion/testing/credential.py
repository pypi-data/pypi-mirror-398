"""
CredentialStore provides mock credential storage for testing nodes
that require vault access.
"""

import os
import threading
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class DatabaseCredential:
    """Database connection parameters."""
    server: str = ""
    port: int = 0
    database: str = ""
    username: str = ""
    password: str = ""


class CredentialStore:
    """
    CredentialStore holds mock credentials for testing.
    Credentials are stored by a key and can be retrieved during tests.
    """

    _instance: Optional['CredentialStore'] = None
    _lock = threading.Lock()

    def __init__(self):
        """Create a new empty CredentialStore."""
        self._credentials: Dict[str, Dict[str, Any]] = {}
        self._mu = threading.RLock()

    @classmethod
    def get_instance(cls) -> Optional['CredentialStore']:
        """Get the global credential store instance."""
        with cls._lock:
            return cls._instance

    @classmethod
    def set_instance(cls, store: Optional['CredentialStore']) -> None:
        """Set the global credential store instance."""
        with cls._lock:
            cls._instance = store

    def set_api_key(self, name: str, api_key: str) -> 'CredentialStore':
        """
        Store an API key credential (category 4).

        Args:
            name: Credential name
            api_key: API key value

        Returns:
            This CredentialStore for chaining
        """
        with self._mu:
            self._credentials[name] = {"value": api_key}
        return self

    def set_login(self, name: str, username: str, password: str) -> 'CredentialStore':
        """
        Store a login credential (category 1).

        Args:
            name: Credential name
            username: Username
            password: Password

        Returns:
            This CredentialStore for chaining
        """
        with self._mu:
            self._credentials[name] = {
                "username": username,
                "password": password,
            }
        return self

    def set_database(self, name: str, config: DatabaseCredential) -> 'CredentialStore':
        """
        Store a database credential (category 5).

        Args:
            name: Credential name
            config: Database configuration

        Returns:
            This CredentialStore for chaining
        """
        with self._mu:
            self._credentials[name] = {
                "server": config.server,
                "port": config.port,
                "database": config.database,
                "username": config.username,
                "password": config.password,
            }
        return self

    def set_document(self, name: str, content: str, filename: str = "") -> 'CredentialStore':
        """
        Store a document credential (category 6).

        Args:
            name: Credential name
            content: Document content
            filename: Optional filename

        Returns:
            This CredentialStore for chaining
        """
        with self._mu:
            data = {"content": content}
            if filename:
                data["filename"] = filename
            self._credentials[name] = data
        return self

    def set_custom(self, name: str, data: Dict[str, Any]) -> 'CredentialStore':
        """
        Store a custom credential with arbitrary data.

        Args:
            name: Credential name
            data: Credential data dictionary

        Returns:
            This CredentialStore for chaining
        """
        with self._mu:
            self._credentials[name] = dict(data)
        return self

    def add_credential(self, name: str, data: Dict[str, Any]) -> 'CredentialStore':
        """
        Add a credential (alias for set_custom).

        Args:
            name: Credential name
            data: Credential data dictionary

        Returns:
            This CredentialStore for chaining
        """
        return self.set_custom(name, data)

    def get(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a credential by name.

        Args:
            name: Credential name

        Returns:
            Credential data, or None if not found
        """
        with self._mu:
            if name in self._credentials:
                return dict(self._credentials[name])
            return None

    def has(self, name: str) -> bool:
        """
        Check if a credential exists.

        Args:
            name: Credential name

        Returns:
            True if exists
        """
        with self._mu:
            return name in self._credentials

    def load_from_env(self, prefix: str, cred_name: str) -> 'CredentialStore':
        """
        Load credentials from environment variables with a prefix.
        Searches for: PREFIX_API_KEY, PREFIX_KEY, PREFIX_TOKEN, PREFIX_VALUE

        Args:
            prefix: Environment variable prefix (e.g., "GEMINI")
            cred_name: Name to store the credential under

        Returns:
            This CredentialStore for chaining
        """
        with self._mu:
            data: Dict[str, Any] = {}
            found = False

            # Map environment variable suffixes to credential keys
            mappings = {
                "_API_KEY": "value",
                "_KEY": "value",
                "_TOKEN": "value",
                "_VALUE": "value",
                "_USERNAME": "username",
                "_USER": "username",
                "_PASSWORD": "password",
                "_PASS": "password",
                "_SERVER": "server",
                "_HOST": "server",
                "_PORT": "port",
                "_DATABASE": "database",
                "_DB": "database",
                "_CONTENT": "content",
            }

            for suffix, cred_key in mappings.items():
                env_key = prefix.upper() + suffix
                env_value = os.environ.get(env_key)

                if env_value:
                    # Handle port as integer
                    if cred_key == "port":
                        try:
                            data[cred_key] = int(env_value)
                        except ValueError:
                            data[cred_key] = env_value
                    else:
                        data[cred_key] = env_value
                    found = True

            if found:
                self._credentials[cred_name] = data

        return self

    def clear(self) -> None:
        """Clear all credentials."""
        with self._mu:
            self._credentials.clear()

    def get_vault_item(self, vault_id: str, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the vault item by vault ID and item ID.
        Used internally by the mock runtime helper.

        Args:
            vault_id: Vault ID
            item_id: Item ID

        Returns:
            Credential data, or None if not found
        """
        # Try item_id first
        result = self.get(item_id)
        if result:
            return result

        # Try vault_id
        result = self.get(vault_id)
        if result:
            return result

        # Try combined key
        combined = f"{vault_id}:{item_id}"
        return self.get(combined)


def load_dotenv(filename: str) -> bool:
    """
    Load environment variables from a .env file.

    Args:
        filename: Path to the .env file

    Returns:
        True if file was loaded, False if not found
    """
    if not os.path.exists(filename):
        return False

    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue

                # Find the first = sign
                eq_index = line.find('=')
                if eq_index <= 0:
                    continue

                key = line[:eq_index].strip()
                value = line[eq_index + 1:].strip()

                # Remove surrounding quotes
                if len(value) >= 2:
                    if (value[0] == '"' and value[-1] == '"') or \
                       (value[0] == "'" and value[-1] == "'"):
                        value = value[1:-1]

                os.environ[key] = value

        return True
    except Exception:
        return False


class _MockRuntimeHelper:
    """Mock runtime helper that provides credentials during testing."""

    def __init__(self, store: CredentialStore):
        self._store = store

    def get_vault_item(self, vault_id: str, item_id: str) -> Optional[Dict[str, Any]]:
        """Get a vault item from the credential store."""
        if self._store:
            return self._store.get_vault_item(vault_id, item_id)
        return None


# Global mock helper reference
_mock_helper: Optional[_MockRuntimeHelper] = None


def init_credentials(store: CredentialStore) -> None:
    """
    Initialize the runtime with mock credentials from the given store.

    This must be called before running tests that use credentials.

    Args:
        store: Credential store to use
    """
    global _mock_helper
    CredentialStore.set_instance(store)
    _mock_helper = _MockRuntimeHelper(store)

    # Patch the runtime to use our mock helper
    try:
        from robomotion import runtime
        runtime._test_helper = _mock_helper
    except (ImportError, AttributeError):
        pass


def clear_credentials() -> None:
    """Clear mock credentials."""
    global _mock_helper
    CredentialStore.set_instance(None)
    _mock_helper = None

    try:
        from robomotion import runtime
        runtime._test_helper = None
    except (ImportError, AttributeError):
        pass


def get_mock_helper() -> Optional[_MockRuntimeHelper]:
    """Get the current mock helper (for internal use)."""
    return _mock_helper
