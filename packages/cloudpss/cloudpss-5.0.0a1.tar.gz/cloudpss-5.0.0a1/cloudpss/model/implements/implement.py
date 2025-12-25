from .diagram import DiagramImplement


class ModelImplement(object):
    """
        实现类
    """
    def __init__(self, implements: dict = {}):
        """
            初始化
        """
        for k, v in implements.items():
            if k == 'diagram':
                self.__dict__[k] = DiagramImplement(v)
            else:
                self.__dict__[k] = v

    def __getitem__(self, attr):
        return super(ModelImplement, self).__getattribute__(attr)

    def toJSON(self):
        """
            类对象序列化为 dict
            :return: dict

             >>> implement.toJSON()
        """
        implements = {**self.__dict__, 'diagram': self.diagram.toJSON()}
        return implements

    def getDiagram(self):
        """
            获取拓扑实现，不存在返回空

            :return: 示意图实例

            >>> implement.getDiagram()
        """

        return getattr(self, 'diagram', None)
