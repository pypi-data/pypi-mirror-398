"""
AI Tools System for Robomotion Python SDK.

This module provides support for exposing Python nodes as AI tools
that can be called by LLM agents in cross-language scenarios.

The AI Tools system allows any Python node to be used as an AI tool by:
1. Adding a Tool field with tool metadata
2. Adding aiScope option to variables the designer can expose to AI
3. Zero additional code needed - existing on_message logic works for both RPA and AI contexts
"""

import json
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class Tool:
    """
    Marker class that indicates a node can be used as an AI tool.

    The actual tool specification and JSON schema generation happens
    during spec generation. This class provides metadata for the tool.

    Usage:
        class MyNode(Node):
            tool = Tool(name="my_tool", description="Does something useful")

            inInput = InVariable(
                title="Input",
                type="string",
                aiScope=True  # Expose to AI
            )
            outResult = OutVariable(
                title="Result",
                type="string",
                aiScope=True  # Expose to AI
            )
    """
    name: str = ""
    description: str = ""


def is_tool_request(ctx) -> bool:
    """
    Check if the current message is a tool request from an LLM Agent.

    Args:
        ctx: Message context

    Returns:
        True if this is a tool request, False otherwise
    """
    msg_type = ctx.get("__message_type__")
    return msg_type == "tool_request"


def get_tool_parameters(ctx) -> Dict[str, Any]:
    """
    Extract tool parameters from the message context.

    When an LLM Agent calls a tool, parameters are passed in the
    __parameters__ field of the message context.

    Args:
        ctx: Message context

    Returns:
        Dictionary of parameter name -> value
    """
    if not is_tool_request(ctx):
        return {}

    params = ctx.get("__parameters__")
    if params and isinstance(params, dict):
        return params
    return {}


def tool_response(ctx, status: str, data: Optional[Dict[str, Any]] = None, error_msg: str = "") -> bool:
    """
    Send a response back to the LLM Agent and prevent message flow to next node.

    This function should be called from within a node's on_message handler
    when processing a tool request. It sends the result back to the calling
    LLM Agent and prevents the message from flowing to connected nodes.

    Args:
        ctx: Message context
        status: Response status ("success" or "error")
        data: Dictionary of output data to return to the LLM Agent
        error_msg: Error message if status is "error"

    Returns:
        True if response was sent, False if not a tool request

    Usage:
        async def on_message(self, ctx):
            if is_tool_request(ctx):
                # Get input parameters
                params = get_tool_parameters(ctx)
                input_value = params.get("input", "")

                # Do the work
                result = process(input_value)

                # Send response back to LLM Agent
                tool_response(ctx, "success", {"result": result})
                return

            # Normal RPA processing
            ...
    """
    if not is_tool_request(ctx):
        return False

    caller_id = ctx.get("__tool_caller_id__")
    agent_node_id = ctx.get("__agent_node_id__")

    # Build response data
    response_data = {
        "__message_type__": "tool_response",
        "__tool_caller_id__": caller_id,
        "__tool_status__": status,
    }

    # Copy essential fields from original message
    if ctx.get("id"):
        response_data["id"] = ctx.get("id")
    if ctx.get("session_id"):
        response_data["session_id"] = ctx.get("session_id")
    if ctx.get("query"):
        response_data["query"] = ctx.get("query")

    # Add error or data
    if error_msg:
        response_data["__tool_error__"] = error_msg
    if data:
        response_data["__tool_data__"] = data

    # Send response back to LLM Agent via emit_input
    if agent_node_id and isinstance(agent_node_id, str):
        from robomotion.event import Event
        response_bytes = json.dumps(response_data).encode()
        Event.emit_input(agent_node_id, response_bytes)

    # Prevent message flow by clearing context
    ctx.set_raw(None)

    return True


class ToolInterceptor:
    """
    Wrapper that automatically handles tool requests for a node.

    The ToolInterceptor wraps a node's message handler to automatically:
    1. Detect tool requests via __message_type__ == "tool_request"
    2. Extract parameters from __parameters__ in message context
    3. Call the original on_message handler
    4. Auto-collect output variables and send response via tool_response

    This is typically applied automatically during node registration
    if the node has a Tool field.
    """

    def __init__(self, node):
        """
        Create a tool interceptor for a node.

        Args:
            node: The node instance to wrap
        """
        self.node = node
        self.has_tool = hasattr(node, 'tool') and isinstance(getattr(node, 'tool'), Tool)

    async def on_create(self):
        """Delegate to original node's on_create."""
        return await self.node.on_create()

    async def on_message(self, ctx):
        """
        Handle message, intercepting tool requests if applicable.

        For tool requests on tool-enabled nodes:
        1. Call the original handler to do the work
        2. If no explicit tool_response was sent, auto-send one
        """
        if self.has_tool and is_tool_request(ctx):
            return await self._handle_tool_request(ctx)

        # Pass through to original handler for normal processing
        return await self.node.on_message(ctx)

    async def on_close(self):
        """Delegate to original node's on_close."""
        return await self.node.on_close()

    async def _handle_tool_request(self, ctx):
        """
        Automatically process tool requests.

        Calls the original handler and sends a default response
        if one wasn't explicitly sent.
        """
        error = None
        try:
            await self.node.on_message(ctx)
        except Exception as e:
            error = str(e)

        # Check if tool_response was already called (ctx.data would be None)
        if not self._has_tool_response_been_sent(ctx):
            if error:
                tool_response(ctx, "error", None, error)
            else:
                # Collect output variables automatically
                output_data = self._collect_output_variables(ctx)
                tool_response(ctx, "success", output_data, "")

    def _has_tool_response_been_sent(self, ctx) -> bool:
        """Check if tool_response was already called."""
        try:
            raw = ctx.get_raw()
            return raw is None
        except Exception:
            return True

    def _collect_output_variables(self, ctx) -> Dict[str, Any]:
        """
        Automatically collect output variable values from the node.

        Looks for OutVariable fields and collects their values
        from the message context.
        """
        from robomotion.variable import OutVariable

        output_data = {}

        # Iterate through node attributes to find OutVariable fields
        for attr_name in dir(self.node):
            if attr_name.startswith('_'):
                continue

            attr = getattr(self.node, attr_name, None)
            if isinstance(attr, OutVariable):
                # Get the variable name
                var_name = getattr(attr, 'name', attr_name)
                if var_name:
                    # Try to get the value from context
                    value = ctx.get(var_name)
                    if value is not None:
                        output_data[var_name] = value

        # If no output variables found, return basic status
        if not output_data:
            output_data["status"] = "completed"

        return output_data


def wrap_with_tool_interceptor(node):
    """
    Wrap a node with ToolInterceptor if it has a Tool field.

    This function is called during node registration to automatically
    add tool handling capabilities to nodes that have a Tool field.

    Args:
        node: The node instance to potentially wrap

    Returns:
        The original node or a ToolInterceptor-wrapped version
    """
    if hasattr(node, 'tool') and isinstance(getattr(node, 'tool'), Tool):
        return ToolInterceptor(node)
    return node
