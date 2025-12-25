import copy
import re

from .result import Result


class PowerFlowResult(Result):
    """
        潮流结果视图， 

        提供快速获取 buses 和 branches 的接口，并提供潮流写入项目的接口

        该类只提供潮流仿真时使用

    """

    def getBuses(self):
        """
            获取所有的 buses 数据

            >>> view.getBuses()
            [...]
        """
        result = []
        pattern = re.compile("value=\"(.*)\"")
        data = self.getMessagesByKey('buses-table')
        if len(data) == 0:
            return []
        table = copy.deepcopy(data[0])
        columns = table['data']['columns']
        for column in columns:
            if column['type'] == 'html':
                data = column['data']
                for i in range(len(data)):
                    if data[i] != '':
                        s = pattern.findall(data[i])
                        data[i] = s[0].replace('/', '')

        result.append(table)
        return result


    def getBranches(self):
        """
            获取潮流结果 branches 数据

            >>> view.getBranches()
            [...]
        """

        result = []
        pattern = re.compile("value=\"(.*)\"")
        data = self.getMessagesByKey('branches-table')
        if len(data) == 0:
            return []
        table = copy.deepcopy(data[0])

        columns = table['data']['columns']
        for column in columns:
            if column['type'] == 'html':
                data = column['data']
                for i in range(len(data)):
                    if data[i] != '':
                        s = pattern.findall(data[i])
                        data[i] = s[0].replace('/', '')

        result.append(table)
        return result
    
    def powerFlowModify(self, model):
        """
            潮流数据写入 model

            >>> view.powerFlowModify(model)
        """

        data = self.getMessagesByKey('power-flow-modify')
        if len(data) == 0:
            raise Exception('未找到到数据')
        self.modify(data[0], model)