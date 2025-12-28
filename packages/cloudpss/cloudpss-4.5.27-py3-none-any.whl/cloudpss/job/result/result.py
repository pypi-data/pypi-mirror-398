

import sys
from deprecated import deprecated
from ..messageStreamSender import MessageStreamSender
from ..messageStreamReceiver import MessageStreamReceiver

class Result(object):
    """
        结果视图基类，提供基础的结果获取接口
    """
    def __init__(self,job, receiver:MessageStreamReceiver,sender:MessageStreamSender=None) -> None:
        """
            初始化
        """
        self.result = {}
        self._receiver = receiver
        self.__sender = sender
        self.__logsIndex = 0
        self.job=job    
        
        
    @property
    def _sender(self):
        """
            获取发送器对象

            :returns: 发送器对象

            >>> sender= result.sender()
        """
        if self.__sender is None:
            self.__sender = self.job.write()
        return self.__sender
    
    async def receive(self):
        async for msg in self._receiver:
            yield msg
            
    def __len__(self):
        return len(self._receiver)

    def __iter__(self):
        return self
    def __next__(self):
        return next(self._receiver)
        
    def __deepModify(self, dict1, dict2):

        for key, val in dict1.items():
            if type(val) is dict:
                if type(dict2) is dict and dict2.get(key, None) is None:
                    dict2[key] = val
                else:
                    self.__deepModify(val, dict2[key])
            else:
                dict2[key] = val
                
    def modify(self, data, model):
        """
            通过指定消息修改算例文件

            :params: data 消息字典 {}
            :params: model  项目

            >>> message= view.modify(data,model)

        """
        modifyData = data['data']
        payload = modifyData['payload']
        self.__deepModify(payload, model)
    
    def getMessagesByKey(self, key):
        """
            获取指定 key 的消息数据

            :params key: 数据key

            :returns: 对应 key 的数据数组

            >>> message= db.getMessagesByKey('log')
        """

        result = []
        for val in self._receiver.messages:
            if val.get('key', None) == key:
                result.append(val)
        return result

    def getMessagesByType(self, type):
        """
            获取指定类型的消息数据

            :params type: 数据类型

            :returns: 对应类型的数据数组

            >>> message= db.getMessagesByType('log')
        """
        result = []
        for val in self._receiver:
            if val['type'] == type:
                result.append(val)
        return result

    def getMessage(self, index):
        """
            获取指定位置的消息数据

            :params index: 数据的位置信息

            :returns: 消息数据

            >>> message= db.getMessage(1)
        """
        return self._receiver.messages[index]

    def getMessages(self):
        """
            获取所有消息数据

            :returns: 消息数据数组
        """
        return self._receiver.messages
    
    
    def getLogs(self):
        '''
            获取当前任务的日志

            >>>logs= result.getLogs()
            {...}
        '''
        result = []
        length = len(self._receiver.messages)
        if (length > self.__logsIndex):
            for num in range(self.__logsIndex, length):
                val = self.getMessage(num)
                if val['type'] == 'log':
                    result.append(val)
            self.__logsIndex = length
        return result
    
    def getMessageLength(self):
        """
            获取消息数据的长度

            :returns: 消息数据的长度
        """
        return len(self._receiver.messages)
        
    
    def waitFor(self,timeOut=sys.maxsize):
        """
            阻塞方法，直到任务完成

            :params timeOut: 超时时间
        """
        return self._receiver.waitFor(timeOut)
    
    @property
    @deprecated(version='3.0', reason="该方法将在 5.0 版本移除")
    def db(self):
        """
            获取数据库对象

            :returns: 数据库对象
        """
        return self._receiver
    
    def pop(self,index=-1):
        """
            pop 出缓存中的消息

            :returns: 消息数据
        """
        
        return self._receiver.messages.pop(index)