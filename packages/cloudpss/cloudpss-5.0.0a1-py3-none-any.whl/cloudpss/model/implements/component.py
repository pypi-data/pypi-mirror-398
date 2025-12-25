class Component(object):
    """
        元件类

        实例变量说明：

        definition 元件定义， 连接线没有definition

        args 元件参数数据，连接线没有参数数据

        pins 元件引脚数据，连接线没有引脚数据

        shapes diagram-component 表示元件，diagram-edge 表示连接线

    """

    def __init__(self, diagram: dict = {}):
        self.__dict__.update(diagram)

    def __getitem__(self, attr):
        return super(Component, self).__getattribute__(attr)

    def toJSON(self):
        """
            类对象序列化为 dict
            :return: dict

            >>> comp.toJSON()
        """
        cells = {**self.__dict__}

        return cells
