"""
Quick provides a high-level testing API for Robomotion nodes.
It auto-configures variables based on their type and naming conventions.
"""

import re
from typing import Any, Dict, Optional

from robomotion.testing.context import MockContext
from robomotion.testing.harness import Harness


class Quick:
    """
    Quick provides a simplified interface for common testing patterns.
    It automatically configures variables based on naming conventions when possible.

    Example:
        node = MyNode()
        q = Quick(node)
        q.set_custom('in_text', 'Hello, world!')
        q.set_credential('opt_api_key', 'api_key', 'api_key')

        err = q.run()
        result = q.get_output('text')
    """

    def __init__(self, node):
        """
        Create a new Quick helper for testing a node.
        Automatically configures all variable fields.

        Args:
            node: The node instance to test
        """
        if node is None:
            raise ValueError("node cannot be None")

        self._node = node
        self._harness = Harness(node)
        self._variable_attrs: Dict[str, Any] = {}

        self._auto_configure_variables()

    @property
    def harness(self) -> Harness:
        """Get the underlying Harness for advanced operations."""
        return self._harness

    @property
    def context(self) -> MockContext:
        """Get the underlying MockContext."""
        return self._harness.context

    def set_input(self, name: str, value: Any) -> 'Quick':
        """
        Set an input value in the message context.

        Args:
            name: Path in the message context
            value: Value to set

        Returns:
            This Quick for chaining
        """
        self._harness.with_input(name, value)
        return self

    def set_inputs(self, inputs: Dict[str, Any]) -> 'Quick':
        """
        Set multiple input values in the message context.

        Args:
            inputs: Dictionary of path->value pairs

        Returns:
            This Quick for chaining
        """
        self._harness.with_inputs(inputs)
        return self

    def set_custom(self, field_name: str, value: Any) -> 'Quick':
        """
        Set a Custom scope value for a field by its attribute name.

        Args:
            field_name: Attribute name (e.g., "in_text", "opt_model")
            value: Value to set

        Returns:
            This Quick for chaining
        """
        variable = self._get_variable(field_name)
        if variable:
            self._harness.configure_custom_input(variable, value)
        return self

    def configure_variable(self, field_name: str, scope: str, name: str) -> 'Quick':
        """
        Manually configure a variable's scope and name by field name.

        Args:
            field_name: Attribute name
            scope: Scope (Message, Custom, etc.)
            name: Variable name or value

        Returns:
            This Quick for chaining
        """
        variable = self._get_variable(field_name)
        if variable:
            self._harness.configure_in_variable(variable, scope, name)
        return self

    def set_credential(self, field_name: str, vault_id: str, item_id: str) -> 'Quick':
        """
        Set a Credential field with vault and item IDs.

        Args:
            field_name: Attribute name of the Credential field
            vault_id: Vault ID (or credential name in CredentialStore)
            item_id: Item ID (or same as vault_id for simple lookup)

        Returns:
            This Quick for chaining
        """
        credential = self._get_variable(field_name)
        if credential:
            self._harness.configure_credential(credential, vault_id, item_id)
        return self

    def run(self) -> Optional[Exception]:
        """
        Run OnMessage on the node.

        Returns:
            Exception if any, None on success
        """
        return self._harness.run()

    def run_full(self) -> Optional[Exception]:
        """
        Run the full lifecycle: OnCreate, OnMessage, OnClose.

        Returns:
            Exception if any, None on success
        """
        return self._harness.run_full()

    async def run_async(self) -> Optional[Exception]:
        """
        Run OnMessage on the node asynchronously.

        Returns:
            Exception if any, None on success
        """
        return await self._harness.run_async()

    def get_output(self, name: str) -> Any:
        """
        Get an output value from the context.

        Args:
            name: Output name/path

        Returns:
            The value, or None if not found
        """
        return self._harness.get_output(name)

    def output(self, name: str) -> Any:
        """
        Get an output value from the context (alias for get_output).

        Args:
            name: Output name/path

        Returns:
            The value, or None if not found
        """
        return self._harness.get_output(name)

    def output_string(self, name: str) -> str:
        """Get a string output value."""
        return self._harness.get_output_string(name)

    def output_int(self, name: str) -> int:
        """Get an integer output value."""
        return self._harness.get_output_int(name)

    def output_float(self, name: str) -> float:
        """Get a float output value."""
        return self._harness.get_output_float(name)

    def output_bool(self, name: str) -> bool:
        """Get a boolean output value."""
        return self._harness.get_output_bool(name)

    def get_all_outputs(self) -> Dict[str, Any]:
        """Get all output values from the context."""
        return self._harness.get_all_outputs()

    def reset(self) -> 'Quick':
        """
        Reset the context for reuse.

        Returns:
            This Quick for chaining
        """
        self._harness.reset()
        return self

    def _auto_configure_variables(self) -> None:
        """Auto-configure all variable fields on the node."""
        for attr_name in dir(self._node):
            # Skip private attributes and methods
            if attr_name.startswith('_'):
                continue

            try:
                attr = getattr(self._node, attr_name)
            except AttributeError:
                continue

            # Skip methods and non-variable objects
            if callable(attr):
                continue

            # Check if it's a variable type
            if self._is_variable_type(attr):
                self._variable_attrs[attr_name] = attr
                self._configure_from_naming(attr_name, attr)

    def _is_variable_type(self, obj) -> bool:
        """Check if an object is a Variable type."""
        if obj is None:
            return False

        type_name = type(obj).__name__
        return any(name in type_name for name in [
            'InVariable', 'OutVariable', 'OptVariable',
            'Variable', 'Credentials', 'Credential'
        ])

    def _configure_from_naming(self, attr_name: str, variable) -> None:
        """Configure a variable based on its naming convention."""
        # Determine default scope and name based on naming convention
        scope = "Message"
        name = self._get_default_name(attr_name)

        # Check if it has input/output/option attributes
        if hasattr(variable, 'input') and variable.input:
            scope = "Message"
        elif hasattr(variable, 'output') and variable.output:
            scope = "Message"
        elif hasattr(variable, 'option') and variable.option:
            scope = "Custom"

        # Check for customScope attribute
        if hasattr(variable, 'customScope') and variable.customScope:
            scope = "Custom"

        # Check for messageScope attribute
        if hasattr(variable, 'messageScope') and variable.messageScope:
            scope = "Message"

        # Configure the variable
        self._set_variable_scope_name(variable, scope, name)

    def _get_default_name(self, attr_name: str) -> str:
        """
        Get the default name for a variable based on its attribute name.
        Converts "in_user_name" -> "userName", "out_result" -> "result", etc.
        """
        name = attr_name

        # Remove common prefixes
        prefixes = ['in_', 'out_', 'opt_', 'In', 'Out', 'Opt']
        for prefix in prefixes:
            if name.startswith(prefix):
                name = name[len(prefix):]
                break

        # Convert snake_case to camelCase
        if '_' in name:
            parts = name.split('_')
            name = parts[0].lower() + ''.join(p.capitalize() for p in parts[1:])
        else:
            # Just lowercase the first character
            if name:
                name = name[0].lower() + name[1:]

        return name

    def _get_variable(self, field_name: str) -> Any:
        """Get a variable by field name."""
        # Try direct lookup
        if field_name in self._variable_attrs:
            return self._variable_attrs[field_name]

        # Try getting from node
        if hasattr(self._node, field_name):
            return getattr(self._node, field_name)

        # Try alternative naming (camelCase vs snake_case)
        snake_case = self._to_snake_case(field_name)
        if hasattr(self._node, snake_case):
            return getattr(self._node, snake_case)

        camel_case = self._to_camel_case(field_name)
        if hasattr(self._node, camel_case):
            return getattr(self._node, camel_case)

        return None

    def _set_variable_scope_name(self, variable, scope: str, name: Any) -> None:
        """Set the scope and name on a variable."""
        # Handle different variable implementations
        if hasattr(variable, '_Variable__scope'):
            variable._Variable__scope = scope
        elif hasattr(variable, '_scope'):
            variable._scope = scope

        if hasattr(variable, '_Variable__name'):
            variable._Variable__name = name
        elif hasattr(variable, '_name'):
            variable._name = name

    def _to_snake_case(self, name: str) -> str:
        """Convert camelCase to snake_case."""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _to_camel_case(self, name: str) -> str:
        """Convert snake_case to camelCase."""
        components = name.split('_')
        return components[0] + ''.join(x.capitalize() for x in components[1:])
