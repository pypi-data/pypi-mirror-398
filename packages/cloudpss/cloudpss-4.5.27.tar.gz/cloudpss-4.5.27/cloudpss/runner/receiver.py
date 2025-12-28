import websocket
import requests
import json
import os
import traceback
from urllib.parse import urlparse, urlunparse
from .transform import Transformer
import datetime
import pytz
import ssl
import time

utc_tz = pytz.timezone('UTC')


class Receiver(object):
    '''
        socket 接收服务
    '''
    def __init__(self, taskId, db, url = None, **kwargs):
        '''
            连接远程服务器接收结果数据

            :params: taskId 邮箱
            :params: result 结果实例
            :params: url 地址

        '''

        self.isOpen = False
        self.taskId = taskId
        self.transformer = Transformer(db.job)
        if url is None:
            baseUrl = os.environ.get('CLOUDPSS_API_URL',
                                     'https://cloudpss.net/')
            u = list(urlparse(baseUrl))
            u[0] = 'wss' if u[0] == 'https' else 'ws'
            u[1] = u[1].replace('api.', '')
            u[2] = u[0] + '/'
            url = urlunparse(u)
        self.url = url
        self.db = db
        self._status = 0
        self.error = None

    def close(self, ws):
        ws.close()

    def status(self):
        return self._status

    def on_message(self, ws, message):
        '''
            消息接收处理

            :params: ws socket实例
            :params: message 接收到的数据

            heartbeat ws心跳服务
            __testData__
        '''
        if message == b'--heartbeat--' or message == b'__testData__' or message == '__testData__' or message == '--heartbeat--':
            return
        try:
            payload = json.loads(message)
            payload['when'] = datetime.datetime.now()
            msg = payload
            try:
                if ('version' in payload and payload['version'] == 1):
                    self.db.storeMessage(payload)
                else:
                    msg = self.transformer.transform(payload)
                    if msg == None:
                        pass

                    elif type(msg) is list:
                        for plot in msg:
                            self.db.storeMessage(plot)
                            pass
                    else:
                        self.db.storeMessage(msg)

            except Exception as e:
                msg = {
                    'type': 'log',
                    'verb': 'create',
                    'version': 1,
                    'data': {
                        'level': 'error',
                        'content': traceback.format_exc(),
                    },
                }
                self.db.storeMessage(msg)

            if msg and type(msg) is dict and msg.get('type',
                                                     None) == 'terminate':
                self.db.finished = datetime.datetime.now(tz=utc_tz).isoformat()
                self._status = 1
                self.close(ws)

        except Exception as e:
            print(e)

    def on_error(self, ws, error):
        self._status = -1
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

    def on_close(self, *args,**kwargs):
        msg = {
            'type': 'log',
            'verb': 'create',
            'version': 1,
            'data': {
                'level': 'error',
                'content': "websocket closed",
            },
        }
        self.db.storeMessage(msg)

    def on_open(self, ws):
        self.isOpen = True

    def connect(self):
        self._status = 0
        url = requests.compat.urljoin(self.url, self.taskId)  # type: ignore
        self.ws = websocket.WebSocketApp(url + '?subscribe-broadcast',
                                         on_open=self.on_open,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close)
        self.ws.run_forever()
