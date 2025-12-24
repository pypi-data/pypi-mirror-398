from robomotion.runtime import Runtime
import asyncio

class NodeFactory:
    def __init__(self, c):
        self.c = c

    async def on_create(self, config: bytes):
        node = Runtime.deserialize(config, self.c)
        Runtime.add_node(node.guid, node)
        await node.on_create()
