"""Capabilities module for robomotion.

This module re-exports IsLMOCapable from runtime for backwards compatibility.
The actual implementation is in runtime.py to avoid circular imports.
"""
import sys

# Re-export from runtime for backwards compatibility
from robomotion.runtime import IsLMOCapable, MINIMUM_ROBOT_VERSION


class Capability:
    CapabilityLMO = 1 << 0


capabilities = []


def add_capability(capability):
    capabilities.append(capability)


def get_capabilities():
    _capabilities = sys.maxsize
    for cap in capabilities:
        _capabilities &= cap
    return _capabilities


def init_capabilities():
    add_capability(Capability.CapabilityLMO)


init_capabilities()
