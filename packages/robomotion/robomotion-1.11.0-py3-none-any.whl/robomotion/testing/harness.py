"""
Harness provides a low-level testing API for Robomotion nodes.
It allows full control over variable configuration and node lifecycle.
"""

import asyncio
from typing import Any, Dict, Optional, TypeVar

from robomotion.testing.context import MockContext

T = TypeVar('T')


class Harness:
    """
    Harness provides a testing harness for Robomotion nodes.
    It allows setting up input values, configuring variables, running the node,
    and asserting on output values.
    """

    def __init__(self, node):
        """
        Create a new test harness for the given node.

        Args:
            node: The node instance to test
        """
        self._node = node
        self._context = MockContext()
        self._inputs: Dict[str, Any] = {}
        self._create_called = False

    @property
    def context(self) -> MockContext:
        """Get the underlying MockContext."""
        return self._context

    def with_input(self, name: str, value: Any) -> 'Harness':
        """
        Set an input value in the message context.

        Args:
            name: Path in the message context
            value: Value to set

        Returns:
            This Harness for chaining
        """
        self._inputs[name] = value
        self._context.set(name, value)
        return self

    def with_inputs(self, inputs: Dict[str, Any]) -> 'Harness':
        """
        Set multiple input values in the message context.

        Args:
            inputs: Dictionary of path->value pairs

        Returns:
            This Harness for chaining
        """
        if inputs:
            for name, value in inputs.items():
                self.with_input(name, value)
        return self

    def with_context(self, ctx: MockContext) -> 'Harness':
        """
        Use a custom MockContext instead of the default empty one.

        Args:
            ctx: Custom context to use

        Returns:
            This Harness for chaining
        """
        self._context = ctx if ctx else MockContext()
        return self

    def configure_in_variable(self, variable, scope: str, name: str) -> 'Harness':
        """
        Configure an InVariable with scope and name.

        Args:
            variable: The variable to configure
            scope: Scope (Message, Custom, etc.)
            name: Variable name or path

        Returns:
            This Harness for chaining
        """
        if variable:
            self._set_variable_scope_name(variable, scope, name)
        return self

    def configure_out_variable(self, variable, scope: str, name: str) -> 'Harness':
        """
        Configure an OutVariable with scope and name.

        Args:
            variable: The variable to configure
            scope: Scope (Message, Custom, etc.)
            name: Variable name or path

        Returns:
            This Harness for chaining
        """
        if variable:
            self._set_variable_scope_name(variable, scope, name)
        return self

    def configure_opt_variable(self, variable, scope: str, name: str) -> 'Harness':
        """
        Configure an OptVariable with scope and name.

        Args:
            variable: The variable to configure
            scope: Scope (Message, Custom, etc.)
            name: Variable name or path

        Returns:
            This Harness for chaining
        """
        if variable:
            self._set_variable_scope_name(variable, scope, name)
        return self

    def configure_custom_input(self, variable, value: Any) -> 'Harness':
        """
        Configure a variable for Custom scope with a direct value.
        For Custom scope, the name field holds the actual value.

        Args:
            variable: The variable to configure
            value: The value to set

        Returns:
            This Harness for chaining
        """
        if variable:
            normalized_value = self._normalize_numeric_value(value)
            self._set_variable_scope_name(variable, "Custom", normalized_value)
        return self

    def configure_credential(self, credential, vault_id: str, item_id: str) -> 'Harness':
        """
        Configure a Credential field with vault and item IDs.

        Args:
            credential: The credential to configure
            vault_id: Vault ID
            item_id: Item ID

        Returns:
            This Harness for chaining
        """
        if credential:
            # Set the credential's vaultId and itemId
            if hasattr(credential, '_Credentials__vaultId'):
                credential._Credentials__vaultId = vault_id
            elif hasattr(credential, 'vaultId'):
                credential.vaultId = vault_id

            if hasattr(credential, '_Credentials__itemId'):
                credential._Credentials__itemId = item_id
            elif hasattr(credential, 'itemId'):
                credential.itemId = item_id
        return self

    def run(self) -> Optional[Exception]:
        """
        Run OnMessage on the node.
        Calls OnCreate first if not already called.

        Returns:
            Exception if any, None on success
        """
        try:
            if not self._create_called:
                if asyncio.iscoroutinefunction(self._node.on_create):
                    asyncio.get_event_loop().run_until_complete(self._node.on_create())
                else:
                    self._node.on_create()
                self._create_called = True

            if asyncio.iscoroutinefunction(self._node.on_message):
                asyncio.get_event_loop().run_until_complete(
                    self._node.on_message(self._context)
                )
            else:
                self._node.on_message(self._context)

            return None
        except Exception as e:
            return e

    def run_with_create(self) -> Optional[Exception]:
        """
        Run OnCreate explicitly, then OnMessage.

        Returns:
            Exception if any, None on success
        """
        try:
            if asyncio.iscoroutinefunction(self._node.on_create):
                asyncio.get_event_loop().run_until_complete(self._node.on_create())
            else:
                self._node.on_create()
            self._create_called = True

            if asyncio.iscoroutinefunction(self._node.on_message):
                asyncio.get_event_loop().run_until_complete(
                    self._node.on_message(self._context)
                )
            else:
                self._node.on_message(self._context)

            return None
        except Exception as e:
            return e

    def run_full(self) -> Optional[Exception]:
        """
        Run the full lifecycle: OnCreate, OnMessage, OnClose.

        Returns:
            Exception if any, None on success
        """
        try:
            if asyncio.iscoroutinefunction(self._node.on_create):
                asyncio.get_event_loop().run_until_complete(self._node.on_create())
            else:
                self._node.on_create()
            self._create_called = True

            if asyncio.iscoroutinefunction(self._node.on_message):
                asyncio.get_event_loop().run_until_complete(
                    self._node.on_message(self._context)
                )
            else:
                self._node.on_message(self._context)

            if asyncio.iscoroutinefunction(self._node.on_close):
                asyncio.get_event_loop().run_until_complete(self._node.on_close())
            else:
                self._node.on_close()

            return None
        except Exception as e:
            return e

    async def run_async(self) -> Optional[Exception]:
        """
        Run OnMessage on the node asynchronously.
        Calls OnCreate first if not already called.

        Returns:
            Exception if any, None on success
        """
        try:
            if not self._create_called:
                await self._node.on_create()
                self._create_called = True

            await self._node.on_message(self._context)
            return None
        except Exception as e:
            return e

    def get_output(self, name: str) -> Any:
        """
        Get an output value from the context.

        Args:
            name: Output name/path

        Returns:
            The value, or None if not found
        """
        return self._context.get(name)

    def get_output_string(self, name: str) -> str:
        """Get a string output value."""
        return self._context.get_string(name)

    def get_output_int(self, name: str) -> int:
        """Get an integer output value."""
        return self._context.get_int(name)

    def get_output_float(self, name: str) -> float:
        """Get a float output value."""
        return self._context.get_float(name)

    def get_output_bool(self, name: str) -> bool:
        """Get a boolean output value."""
        return self._context.get_bool(name)

    def get_all_outputs(self) -> Dict[str, Any]:
        """Get all output values from the context."""
        return self._context.get_all()

    def reset(self) -> 'Harness':
        """
        Reset the context and state for reuse.

        Returns:
            This Harness for chaining
        """
        self._context = MockContext()
        self._inputs = {}
        self._create_called = False
        return self

    def _set_variable_scope_name(self, variable, scope: str, name: Any) -> None:
        """Set the scope and name on a variable."""
        # Handle different variable implementations
        # Try private attributes first (Python name mangling)
        if hasattr(variable, '_Variable__scope'):
            variable._Variable__scope = scope
        elif hasattr(variable, '_scope'):
            variable._scope = scope
        elif hasattr(variable, 'scope'):
            # Direct attribute access (property setter)
            try:
                variable.scope = scope
            except AttributeError:
                pass

        if hasattr(variable, '_Variable__name'):
            variable._Variable__name = name
        elif hasattr(variable, '_name'):
            variable._name = name
        elif hasattr(variable, 'name'):
            try:
                variable.name = name
            except AttributeError:
                pass

    def _normalize_numeric_value(self, value: Any) -> Any:
        """Normalize numeric values to match runtime expectations."""
        if value is None:
            return None

        # Python handles numeric types more uniformly than Go/C#
        # but we still normalize for consistency
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return value

        return value
