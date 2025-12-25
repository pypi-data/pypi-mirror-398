import os
import io
from ..utils import fileLoad
import gzip
import yaml
import datetime
import pytz
import random

utc_tz = pytz.timezone('UTC')


class Storage(object):
    """
        消息存储类，

        用于存储接收到的消息数据，并提供数据保存、加载两个数据本地化函数

        提供通过数据类型获取数据，通过数据位置获取数据、和获取当前数据长度的函数

    """
    def __init__(self,
                 key,
                 name,
                 job,
                 config,
                 revision,
                 model,
                 messages=None,
                 finished=None,
                 **kwargs):
        """
            初始化
        """
        self.message = messages if messages is not None else []
        self.taskId = key
        self.end = False
        self.name = name if name is not None else ''.join(
            random.sample([
                'z', 'y', 'x', 'w', 'v', 'u', 't', 's', 'r', 'q', 'p', 'o',
                'n', 'm', 'l', 'k', 'j', 'i', 'h', 'g', 'f', 'e', 'd', 'c',
                'b', 'a'
            ], 5))
        self.job = job
        self.config = config
        self.revision = revision
        self.started = datetime.datetime.now(tz=utc_tz).isoformat()
        self.finished = finished
        self.model = model

    def storeMessage(self, message):
        """
            消息存储 db.storeMessage(message)

            :params message: 需要存储的消息
        """
        self.message.append(message)

    @staticmethod
    def dump(result, file):
        '''
            保存结果到本地文件

            :params: file 保存文件的目录

            >>> Result.dump(result,file)
            {...}
        '''

        data = {
            'key': result.taskId,
            'name': result.name,
            'model': result.model,
            'job': result.job,
            'config': result.config,
            'status': 'succeeded',
            'revision': result.revision,
            'messages': result.message,
            'started': result.started,
            'finished': result.finished,
            'queued': datetime.datetime.now(),
            'legacy': []
        }
        data = yaml.dump(data)
        with gzip.open(file, 'w') as output:
            with io.TextIOWrapper(output, encoding='utf-8') as enc:
                enc.write(data)

    @staticmethod
    def load(file):
        """
            加载本地结果文件

            :params: file 文件目录

            :returns: 返回一个项目实例

            >>> result = Result.load('C:\\Users\\dps-dm\\cloudpss-sdk\\result\\424111.cjob')

        """

        if not os.path.exists(file):
            raise FileNotFoundError('未找到文件')
        data = fileLoad(file)
        result = Storage(**data)
        return result

    def getMessagesByType(self, type):
        """
            获取指定类型的消息数据

            :params type: 数据类型

            :returns: 对应类型的数据数组

            >>> message= db.getMessagesByType('log')
        """

        result = []
        for val in self.message:
            if val['type'] == type:
                result.append(val)
        return result

    def getMessagesByKey(self, key):
        """
            获取指定 key 的消息数据

            :params key: 数据key

            :returns: 对应 key 的数据数组

            >>> message= db.getMessagesByKey('log')
        """

        result = []
        for val in self.message:
            if val.get('key', None) == key:
                result.append(val)
        return result

    def getMessageLength(self):
        """
            获取指定消息的长度

            :returns: 数据长度

            >>> length= db.getMessageLength()
        """
        return len(self.message)

    def getMessage(self, index):
        """
            获取指定位置的消息数据

            :params index: 数据的位置信息

            :returns: 消息数据

            >>> message= db.getMessage(1)
        """
        return self.message[index]
