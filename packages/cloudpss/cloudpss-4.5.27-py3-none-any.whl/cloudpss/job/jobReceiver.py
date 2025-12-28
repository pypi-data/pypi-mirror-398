from deprecated import deprecated
class JobReceiver(object):
    messages = []
    index = 0

    def __init__(self):
        self.index = 0
        self.messages = []

    def __len__(self):
        return len(self.messages)

    def __iter__(self):
        return self

    def __next__(self):
        maxLength = len(self.messages)
        if self.index < maxLength:
            message = self.messages[self.index]
            self.index += 1
            return message
        raise StopIteration()

    def result(self, resultType):
        """
            获取指定类型的视图数据

            :params viewType: 视图类型

            :returns: 对应类型的视图数据

            >>> view= receiver.view(EMTView)
        """
        return resultType(self)
    
    @property
    @deprecated(version='3.0', reason="该方法将在 5.0 版本移除")
    def message(self):
        return self.messages