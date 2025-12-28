
import logging
from typing import IO
from urllib.parse import urlparse
import aiohttp
from cloudpss.job.messageStreamSender import MessageStreamSender as MessageStreamSenderBase


class MessageStreamSender(MessageStreamSenderBase):
    
    
    async def receive_data(self):
        if self.websocket:
            data = await self.websocket.receive()
            if data.type == aiohttp.WSMsgType.TEXT:
                self.__on_message(data.data)
            elif data.type == aiohttp.WSMsgType.CLOSED:
                self.__on_close()
            elif data.type == aiohttp.WSMsgType.ERROR:
                self.__on_error(data.data)
        else:
            logging.info("WebSocket connection not established")
    
    async def connect(self):
        self._status = 0
        if self.job.input is None:
            raise Exception("id is None")
        if self.job.input == "00000000-0000-0000-0000-000000000000":
            return
        u = list(urlparse(self.origin))
        head = "wss" if u[0] == "https" else "ws"

        path = head + "://" + str(u[1]) + "/api/streams/token/" + self.job.input
        logging.info(f"MessageStreamSender data from websocket: {path}")
        async with aiohttp.ClientSession() as session:
            self.websocket = await session.ws_connect(path)
            
    async def write(self, message):
        if self.websocket:
            data = IO.serialize(message, "ubjson", None)
            await self.websocket.send_bytes(data)
        else:
            logging.info("websocket is None")

    