
import time
import threading
import websocket
# ws://10.101.10.45/api/streams/token/fe943635-0dc9-40c8-8a27-39d02af66894

    
class WebsocketClient():
    message = []
    _status=0
    # __init__(self):
    def on_close(self, *args, **kwargs):
        self._status = 1
        print("close")
    def on_error(self,  *args, **kwargs):
        self._status = 1
        print("error",args,kwargs)
    def on_open(self,ws, *args, **kwargs):
        self._status = 1
        print("open")
    def on_message(self,  *args, **kwargs):
        self._status = 0
        print("on_message")
    # websocket
    def connect(self):
        self._status = 0
        path = "ws://www.rpssc.top:52694/api/streams/id/a454e6b7-e677-41df-a4e8-6202ff3cb35e"
        self.ws = websocket.WebSocketApp(
            path,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
        )
        thread = threading.Thread(target=self.ws.run_forever, kwargs={'ping_interval':60,'ping_timeout':5,'reconnect':True})
        thread.setDaemon(True)
        thread.start()
        while not self._status:
            time.sleep(0)
       
def main():
    ws=WebsocketClient()
    ws.connect()
    print("start")
    while ws._status == 0:
        time.sleep(0)
        pass
if __name__ == '__main__':
    main()