import inspect

class Action:
    def __init__(self, name, executor, params=None):
        self.name = name
        self.executor = executor
        self.params = params or []

    async def run(self, **kwargs):
        for p in self.params:
            if p not in kwargs:
                raise ValueError(f"Missing parameter: {p}")

        if inspect.iscoroutinefunction(self.executor):
            return await self.executor(**kwargs)
        else:
            return self.executor(**kwargs)
