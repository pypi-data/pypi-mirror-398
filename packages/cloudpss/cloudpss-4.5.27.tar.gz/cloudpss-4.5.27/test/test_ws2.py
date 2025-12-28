
from aiohttp import ClientSession, WSMsgType
import asyncio
import time
# ws://10.101.10.45/api/streams/token/fe943635-0dc9-40c8-8a27-39d02af66894

    
class WebsocketClient():
    message = []
    _status=0
    # __init__(self):
    def on_closed(self):
        self._status = 1
        
        print("close")
    def on_error(self,msg):
        self._status = 1
        print("error")
    def on_open(self):
        self._status = 0
        print("open")
    # websocket
    def __iter__(self):
        return self

    def __next__(self):
        maxLength = len(self.messages)
        if self.index < maxLength:
            message = self.messages[self.index]
            self.index += 1
            return message
        raise StopIteration()
    
    def __aiter__(self):
        return self
    
    async def receive(self):
        msg = await self.ws.receive()
        if msg.type == WSMsgType.BINARY:
            self.message.append(msg)
        if msg.type == WSMsgType.TEXT:
            self.message.append(msg)
        elif msg.type == WSMsgType.CLOSE:
            print(msg)
        elif msg.type == WSMsgType.CLOSED:
            print(msg)
            self.on_closed()
            await self.session.close()
        elif msg.type == WSMsgType.ERROR:
            self.on_error(msg.data)
        return msg
    async def __anext__(self):
        msg = await self.receive()
        if msg.type in (WSMsgType.CLOSE, WSMsgType.CLOSING, WSMsgType.CLOSED):
            raise StopAsyncIteration
        return msg
        # msg = await self.receive()
        # if msg.type in (WSMsgType.CLOSE, WSMsgType.CLOSING, WSMsgType.CLOSED):
        #     raise StopAsyncIteration
        # return msg 
    
    async def websocket_connect(self,url):
        
        # session = await ClientSession()
        # ws = await session.ws_connect(url)

        self.session=  ClientSession()
        self.ws=  await self.session.ws_connect(url)
                # self.on_open()
                # self.ws=ws
                # async for msg in ws:
                # while True:
        
        # self._status=1
    @property
    async def status(self):
        await self.receive()
        return self._status
        
    def count(self):
        # await asyncio.sleep(0.1)
        # while self._status == 0:
        #     await asyncio.sleep(0.5)
        print(len(self.message))
        print(self._status)
        return self._status
        
    async def create(self):
    #    await self.websocket_connect('ws://10.101.10.45/api/streams/id/bb30285a-7d11-484b-a8b0-4855cf8bf8ed')
        await self.websocket_connect('ws://www.rpssc.top:52694/api/streams/id/1d3b2722-dd65-42c2-ac91-a232e44582c9')
    #    asyncio.create_task(self.websocket_connect('ws://10.101.10.45/api/streams/id/bb30285a-7d11-484b-a8b0-4855cf8bf8ed'))
    
async def main():
    ws=WebsocketClient()
    task=await ws.create()
    # task= ws.websocket_connect('ws://10.101.10.45/api/streams/id/6f6ce77c-48a1-4043-8549-1eb72a1a45c7')
    # print(task)
    # await ws.count()
    # async for msg in ws:
    #     # print(msg)
    #     pass
    
    while (await ws.status == 0):
        # ws.count()
        pass
    #     # time.sleep(0.5)
    #     await asyncio.sleep(0.5)
    # task_list=[asyncio.create_task(ws.count())]
    # await asyncio.wait(task_list)
    # print(x[0].pop().result())
    ws.count()
if __name__ == '__main__':
    
    asyncio.run(main())