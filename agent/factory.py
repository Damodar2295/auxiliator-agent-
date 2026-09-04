"""Graph factory - delegates to generated ``agent.graph.build``."""


class GraphFactory:
    @staticmethod
    async def create():
        from agent.graph import build

        return await build()

    @staticmethod
    def create_intelligence(**components):
        from agent.graph import build_intelligence

        return build_intelligence(**components)
