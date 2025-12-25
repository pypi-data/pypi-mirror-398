import os
from urllib.parse import urlparse
import requests
import websocket
import datetime
import pytz
utc_tz = pytz.timezone('UTC')

from ..utils.IO import IO


class Message(object):

    def __init__(self, id, token):
        self.id = id
        self.token = token


class MessageStreamReceiver(object):
    """消息流读取函数结果"""

    def __init__(self, id, db, **kwargs):
        self.origin = os.environ.get('CLOUDPSS_API_URL',
                                     'https://cloudpss.net/')
        self.id = id
        self.db = db
        self._status = 0
        self.error = None
        self.isOpen = False

    def receive(self, id, fr0m, on_open, on_message, on_error, on_close):
        """
        读取消息流中的数据
        id: 消息流id
        fr0m: 从哪个位置开始读取，如果为0则从头开始读取
        on_open: 连接建立时的回调函数
        on_message: 收到消息时的回调函数
        on_error: 发生错误时的回调函数
        on_close: 连接关闭时的回调函数
        """
        if id is None:
            raise Exception('id is None')
        u = list(urlparse(self.origin))
        head = 'wss' if u[0] == 'https' else 'ws'

        path = head + '://' + str(u[1]) + '/api/streams/id/' + id
        if fr0m is not None:
            path = path + '&from=' + str(fr0m)
        self.ws = websocket.WebSocketApp(path,
                                    on_open=on_open,
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close)
        self.ws.run_forever()
        return self.ws

    ###下面是兼容Receiver部分功能实现
    def on_message(self, ws, message):
        data = IO.deserialize(message, 'ubjson')
        msg = IO.deserialize(data['data'], 'ubjson')
        if "when" not in msg:
            msg['when']= datetime.datetime.now()
        self.db.storeMessage(msg)

    def on_error(self, ws, error):
        msg = {
            'type': 'log',
            'verb': 'create',
            'version': 1,
            'data': {
                'level': 'error',
                'content': "websocket error",
            },
        }
        self.db.storeMessage(msg)
        self.error = error
        self._status = -1


    def on_close(self, ws,*args,**kwargs):
        self.db.finished = datetime.datetime.now(tz=utc_tz).isoformat()
        self._status = 1

    def on_open(self, ws):
        self.isOpen = True

    def close(self, ws):
        ws.close()
        self._status = 1

    def status(self):
        return self._status

    def connect(self):
        self._status = 0
        self.ws = self.receive(self.id, None, self.on_open, self.on_message, self.on_error, self.on_close)


