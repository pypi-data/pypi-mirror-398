# define an asynchronous iterator
import asyncio


class AsyncIterator():
    # constructor, define some state
    def __init__(self):
        self.counter = 0
 
    # create an instance of the iterator
    def __aiter__(self):
        return self
 
    # return the next awaitable
    async def __anext__(self):
        # check for no further items
        if self.counter >= 10:
            raise StopAsyncIteration
        # increment the counter
        self.counter += 1
        await asyncio.sleep(1)
        # return the counter value
        return self.counter

async def testAsync():
    # create an instance of the iterator
    asyncIterator = AsyncIterator()
    # iterate over the async iterator
    async for item in asyncIterator:
        print(item)

if __name__ == "__main__":
    asyncio.run(testAsync())