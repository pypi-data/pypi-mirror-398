"""
Robomotion Python Testing Library

This package provides utilities for unit and integration testing of Robomotion nodes
without requiring the full runtime environment.

Example usage:
    from robomotion.testing import Quick, CredentialStore, load_dotenv, init_credentials

    # In test setup:
    store = CredentialStore()
    load_dotenv('.env')
    store.load_from_env('GEMINI', 'api_key')
    init_credentials(store)

    # In test:
    node = MyNode()
    q = Quick(node)
    q.set_credential('opt_api_key', 'api_key', 'api_key')
    q.set_custom('in_text', 'Hello, world!')

    err = q.run()
    assert err is None

    result = q.get_output('text')
    assert result is not None
"""

from robomotion.testing.context import MockContext
from robomotion.testing.credential import (
    CredentialStore,
    DatabaseCredential,
    load_dotenv,
    init_credentials,
    clear_credentials,
)
from robomotion.testing.harness import Harness
from robomotion.testing.quick import Quick

__all__ = [
    'MockContext',
    'CredentialStore',
    'DatabaseCredential',
    'load_dotenv',
    'init_credentials',
    'clear_credentials',
    'Harness',
    'Quick',
]
