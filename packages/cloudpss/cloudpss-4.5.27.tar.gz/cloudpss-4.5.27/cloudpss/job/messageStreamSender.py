import sys, os
import threading
from urllib.parse import urlparse
sys.path.append(os.path.join(os.path.dirname(__file__), "../"))

import websocket

from cloudpss.utils.IO import IO
import time
import logging
from ..version import __version__

class MessageStreamSender:
    def __init__(self, input,**kwargs):
        super().__init__()
        self.input = input
        self.origin = kwargs.get("baseUrl",None)
        if self.origin is None:
            self.origin =os.environ.get("CLOUDPSS_API_URL", "https://cloudpss.net/")
        self.__hasOpen = False

    def __on_message(self, ws, message):
        logging.debug("on_message", message)

    def __on_error(self, ws, error):
        logging.debug("on_error")

    def __on_close(self, *args, **kwargs):
        # print("on_close")
        time.sleep(0.5)
        self._status = 0
        self.__hasOpen=False

        logging.debug("on_close")

    def __on_open(self,ws):
        self._status = 1
        self.__hasOpen=True
        logging.debug("on_open")
        pass

    def close(self):
        # print("close")
        self._status = 0
        self.ws.close()

    @property
    def status(self):
        return self._status

    def write(self, message):
        data = IO.serialize(message, "ubjson", None)
        self.ws.send(data,websocket.ABNF.OPCODE_BINARY)

    def connect_legacy(self):
        """
        同步方法连接ws
        """
        self._status = 0
        if self.input is None:
            raise Exception("id is None")
        if self.input == "00000000-0000-0000-0000-000000000000":
            return
        u = list(urlparse(self.origin))
        head = "wss" if u[0] == "https" else "ws"

        path = head + "://" + str(u[1]) + "/api/streams/token/" + self.input
        logging.debug(f"MessageStreamSender data from websocket: {path}")

        self.ws = websocket.WebSocketApp(
            path,
            on_open=self.__on_open,
            on_message=self.__on_message,
            on_error=self.__on_error,
            on_close=self.__on_close,
            header={
                "User-Agent": "cloudpss-sdk-python/" + __version__
            }
        )
        thread = threading.Thread(target=self.ws.run_forever, args=(None, None, 6, 3))
        thread.setDaemon(True)
        thread.start()
        while not self.__hasOpen:
            time.sleep(0.2)
        return self.ws

    

    
