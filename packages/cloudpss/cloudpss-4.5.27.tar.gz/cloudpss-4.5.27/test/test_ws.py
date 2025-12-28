from aiohttp import ClientSession, WSMsgType
import asyncio
import time
# ws://10.101.10.45/api/streams/token/fe943635-0dc9-40c8-8a27-39d02af66894

    
class WebsocketClient():
    message = []
    _status=0
    # __init__(self):
    def on_close(self):
        self._status = 1
        print("close")
    def on_error(self,msg):
        self._status = 1
        print("error")
    def on_open(self):
        self._status = 0
        print("open")
    # websocket
    async def websocket_connect(self,url):
        
        # session = await ClientSession()
        # ws = await session.ws_connect(url)

        async with ClientSession() as session:
            async with session.ws_connect(url) as ws:
                self.on_open()
                # async for msg in ws:
                while True:
                    msg = await ws.receive()
                    if msg.type == WSMsgType.BINARY:
                        self.message.append(msg)
                    if msg.type == WSMsgType.TEXT:
                        self.message.append(msg)
                    elif msg.type == WSMsgType.CLOSED:
                        self.on_close()
                        break
                    elif msg.type == WSMsgType.ERROR:
                        self.on_error(msg.data)
                        break
        self._status=1
    @property
    async def status(self):
        await asyncio.sleep(0)
        return self._status
    def count(self):
        # await asyncio.sleep(0.1)
        # while self._status == 0:
        #     await asyncio.sleep(0.5)
        print(len(self.message))
        return self._status
        
    async def create(self):
       asyncio.create_task(self.websocket_connect('ws://www.rpssc.top:52694/api/streams/id/a454e6b7-e677-41df-a4e8-6202ff3cb35e'))
       
async def main():
    ws=WebsocketClient()
    task=await ws.create()
    while (await ws.status == 0):
        pass
    ws.count()  
if __name__ == '__main__':
    
    asyncio.run(main())