import asyncio


class CustomAsyncIterable:
    async def __init__(self, async_func, *args):
        self.async_func = async_func
        self.queue = asyncio.Queue()
        self.index = 0
        self.args = args

    async def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            result = await self.queue.get()
            if result is None:
                raise StopAsyncIteration
            return result
        except asyncio.QueueEmpty:
            tasks = []
            for arg in self.args:
                tasks.append(asyncio.create_task(self.async_func(arg)))
            await asyncio.gather(*tasks)
            for task in tasks:
                await self.queue.put(await task)
            return await self.__anext__()
