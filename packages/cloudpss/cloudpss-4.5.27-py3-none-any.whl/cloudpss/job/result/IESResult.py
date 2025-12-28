import copy
import collections

from cloudpss.job.result.result import Result

class IESResult(Result):
    """
        综合能源结果视图， 

        提供快捷 plot 数据的接口函数，获取到的 plot 数据为合并后的数据格式，不在是接收时分段的数据

        该类只提供 IES 仿真使用

    """
     
    __messageIndex = 0
    def __init__(self,job,receiver,sender) -> None:
        super().__init__(job, receiver, sender)
        self.result =  {'Sankey': []}
        # self._receiver = receiver


    def __readPlotResult(self):
        maxLength = len(self._receiver.messages)
        for i in range(self.__messageIndex,maxLength):
            val = self._receiver.messages[i]
            if val['type'] == 'plot':
                key = val['key']
                if key == 'Sankey':
                    self.result['Sankey'].append(copy.deepcopy(val))
                else:
                    if self.result.get(key, None) is None:
                        self.result[key] = copy.deepcopy(val)
                    else:
                        traces = val['data']['traces']
                        for i in range(len(traces)):
                            v = traces[i]
                            self.result[key]['data']['traces'][i][
                                'x'].extend(v['x'])
                            self.result[key]['data']['traces'][i][
                                'y'].extend(v['y'])
        self.__messageIndex = maxLength
    def getPlotData(self, compID, labelName, traceName='all', index=-1):
        '''
            获取元件ID为compID的元件，对应标签为labelName、图例名称为traceName的plot 数据的第index项

            :params: compID string类型，代表元件的标识符
            :params: labelName string类型，代表plot曲线的分组标签
            :params: traceName string类型，代表Plot曲线对应分组下的图例名称，当为'all'时，返回所有图例的数据
            :params: index int类型，代表对应图例时序数据中的第index项，当小于0时，返回该图例所有的时序数据
            
            :return: dict类型
        '''
        self.__readPlotResult()
        key = compID + '_' + labelName
        if key not in self.result.keys():
            raise Exception('未找到元件标志为{0},对应label为{1}的plot数据'.format(
                compID, labelName))

        traceData = self.result[key]['data']['traces']
        if traceName != 'all':
            traceNameList = [traceName]
        else:
            traceNameList = [
                traceData[i]['name'] for i in range(len(traceData))
            ]

        startIndex = 0
        endIndex = len(traceData[0]['x'])
        if index >= 0:
            startIndex = index
            endIndex = index + 1

        plotData = collections.defaultdict(lambda: {})
        for tName in traceNameList:
            for i in range(len(traceData)):
                dataLen = len(traceData[i]['x'])
                if traceData[i]['name'] == tName:
                    if endIndex > dataLen:
                        raise Exception('请求的index超过了plot数据序列的长度')
                    plotData[tName]['x'] = traceData[i]['x'][
                        startIndex:endIndex]
                    plotData[tName]['y'] = traceData[i]['y'][
                        startIndex:endIndex]

        return plotData
    

    def getSankey(self, index):
        '''
            获取第index个桑基图数据

            >>> result.getSankey(index)
            {...}
        '''
        self.__readPlotResult()
        if index >= len(self.result['Sankey']):
            raise Exception('index超过了桑基图数据序列的长度')
        return self.result['Sankey'][index]
    def getSankeyNum(self):
        '''
            获取桑基图数据序列的长度

            >>> result.getSankeyNum()
        '''
        self.__readPlotResult()
        return len(self.result['Sankey'])
