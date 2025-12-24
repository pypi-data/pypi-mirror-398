# port.py
# Python equivalent of Go's port.go

from typing import List, Dict, Any

# Port is a type alias for a list of GUIDs of connected nodes
class Port(list):
    def __init__(self, direction, position, name, icon=None, color=None, filters=None, order=None):
        super().__init__()
        self.direction = direction
        self.position = position
        self.name = name
        self.icon = icon
        self.color = color
        self.filters = filters if filters is not None else []
        self.order = order
