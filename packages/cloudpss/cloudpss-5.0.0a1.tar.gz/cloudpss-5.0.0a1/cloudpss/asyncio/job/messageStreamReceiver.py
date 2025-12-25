import logging
import os
from urllib.parse import urlparse

from aiohttp import ClientSession, WSMsgType
from cloudpss.asyncio.utils.httpAsyncRequest import websocket_connect
from cloudpss.job.jobReceiver import JobReceiver
from cloudpss.utils.IO import IO


class MessageStreamReceiver(JobReceiver):
    def __init__(self, job, dev=False):
        super().__init__()
        self.job = job
        self.dev = dev
        self.origin = os.environ.get("CLOUDPSS_API_URL", "https://cloudpss.net/")
        
    async def __receive(self):
        """
            读取消息流中的数据
        """
        msg = await self.ws.receive()
        result=None
        if msg.type == WSMsgType.BINARY:
           result=await self.__on_message(msg.data)
        if msg.type == WSMsgType.TEXT:
            result=await self.__on_message(msg.data)
        elif msg.type == WSMsgType.CLOSE:
            self.__on_close(msg)
        elif msg.type == WSMsgType.CLOSED:
           await self.__on_closed()
        elif msg.type == WSMsgType.ERROR:
            self.__on_error(msg.data)
        return result
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        result = await self.__receive()
        if result is None:
            raise StopAsyncIteration
        return result     
        
    def __on_close(self, msg,*args, **kwargs):
        if msg is not None and msg.startswith("CMS_NO_STREAM_ID:"):
            self._status = 1
            msg = {
                "type": "log",
                "version": 1,
                "data": {
                    "level": "critical",
                    "content": "未找到任务的输出流，运行结果可能已被清理。",
                },
            }
            self.messages.append(msg)
            return
            
    async def __on_closed(self, *args, **kwargs):
        logging.debug("MessageStreamReceiver close")
        self._status = 1
        msg = {
            "type": "log",
            "verb": "create",
            "version": 1,
            "data": {
                "level": "info",
                "content": "websocket closed",
            },
        }
        self.messages.append(msg)
        await self.session.close()
        
    async def __on_message(self, message):
        
        data = IO.deserialize(message, "ubjson")
        msg = IO.deserialize(data["data"], "ubjson")
        self.messages.append(msg)
        # print(msg['type'])
        if(msg['type']=='terminate'):
            await self.close(self.ws)
        return msg
    
    def __on_error(self, msg,*args, **kwargs):
        logging.debug("MessageStreamReceiver error")
        msg = {
            "type": "log",
            "verb": "create",
            "version": 1,
            "data": {
                "level": "error",
                "content": "websocket error",
            },
        }
        self.messages.append(msg)
        
    @property
    async def status(self):
        await self.__receive()
        return self._status
    
    async def close(self, ws):
        self._status = 1
        await ws.close()
        
    async def connect(self,**kwargs):
        self._status = 0
        
        if self.job.output is None:
            raise Exception("id is None")
        u = list(urlparse(self.origin))
        head = "wss" if u[0] == "https" else "ws"

        path = head + "://" + str(u[1]) + "/api/streams/id/" + self.job.output
        from_=kwargs.get("from",None)
        if from_ is not None:
            path = path + "&from=" + str(from_)
        logging.info(f"MessageStreamReceiver data from websocket: {path}")
        
        self.session=  ClientSession()
        self.ws=  await self.session.ws_connect(path)