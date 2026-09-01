"""Graph factory - delegates to generated ``agent.graph.build``."""


class GraphFactory:
    @staticmethod
    async def create():
        from agent.graph import build

        return await build()
