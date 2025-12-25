import copy
import re
import collections

from cloudpss.utils.httprequests import request
from .storage import Storage

class Result(object):
    """
        结果处理类，从消息存储库中获取数据，并进行简单的整理

        可迭代器，迭代时按接收顺序返回数据

        >>> for data in result:
                print(data)

        也可以从类的 db 变量，获取数据存储类实例进行操作
    """
    def __init__(self, db):
        """
            初始化
        """
        self.n = 0
        self.db = db
        self.__logsIndex = 0

    @classmethod
    def load(cls, filePath):
        """
            加载本地结果文件

            :params: file 文件目录

            :return: 返回一个结果实例

            >>> result = Result.load('C:\\Users\\dps-dm\\cloudpss-sdk\\result\\424111.cjob')

        """
        db = Storage.load(filePath)

        return cls(db)

    @staticmethod
    def dump(result, file):
        '''
            保存结果到本地文件

            :params: file 保存文件的目录

            >>> Result.dump(file)
            {...}
        '''

        Storage.dump(result.db, file)

    def __iter__(self):
        return self

    def __next__(self):
        maxLength = self.db.getMessageLength()
        if self.n < maxLength:
            message = self.db.getMessage(self.n)
            self.n += 1
            return message
        raise StopIteration()

    def getLogs(self):
        '''
            获取当前任务的日志

            >>>logs= result.getLogs()
            {...}
        '''
        result = []
        length = self.db.getMessageLength()
        if (length > self.__logsIndex):
            for num in range(self.__logsIndex, length):
                val = self.db.getMessage(num)
                if val['type'] == 'log':
                    result.append(val)
            self.__logsIndex = length
        return result

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

            >>> message= result.modify(data,model)

        """
        modifyData = data['data']
        payload = modifyData['payload']
        self.__deepModify(payload, model)

    def getMessagesByType(self, type):
        """
            获取指定类型的消息数据

            

            >>> message= result.getMessagesByType('log')
        """
        return self.db.getMessagesByType(type)


class EMTResult(Result):
    """
        电磁暂态结果处理类，继承 Result， 

        提供快捷 plot 数据的接口函数，获取到的 plot 数据为合并后的数据格式，不在是接收时分段的数据

        该类只提供 EMT 仿真使用

    """
    def __init__(self, *args, **kwargs):
        """
            初始化
        """
        Result.__init__(self, *args, **kwargs)
        self.result = {}
        self.__plotIndex = 0

    def getPlots(self):
        '''
            获取所有的 plots 数据

            >>> result.getPlots()
            {...}
        '''

        length = self.db.getMessageLength()
        if (length > self.__plotIndex):
            for num in range(self.__plotIndex, length):
                val = self.db.getMessage(num)
                if val['type'] == 'plot':
                    key = val['key']
                    if self.result.get(key, None) is None:
                        self.result[key] = copy.deepcopy(val)
                    else:
                        traces = val['data']['traces']
                        for i in range(len(traces)):
                            v = traces[i]
                            self.result[key]['data']['traces'][i]['x'].extend(
                                v['x'])
                            self.result[key]['data']['traces'][i]['y'].extend(
                                v['y'])
            self.__plotIndex = length
        return self.result.values()

    def getPlot(self, index: int):
        '''
            获取指定序号的数据分组

            :params: index 图表位置

            >>> result.getPlot(0)
            {...}
        '''
        self.getPlots()
        if self.result is not None:
            return self.result.get('plot-{0}'.format(int(index)), None)

    def getPlotChannelNames(self, index):
        '''
            获取一组输出分组下的所有通道名称

            :params: index 输出通道位置

            :return: 通道名称数组

            >>>names= result.getPlotChannelNames(0)
            []
        '''
        plot = self.getPlot(int(index))
        if plot is None:
            return None

        return [val['name'] for val in plot['data']['traces']]

    def getPlotChannelData(self, index, channelName):
        '''
            获取一组输出分组下指定通道名称的数据

            :params: index 输出通道位置
            :params: channelName 输出通道名称

            :return: 通道数据, 一个 trace 数据

            >>>channel= result.getPlotChannelData(0，'')
            {...}
        '''
        plot = self.getPlot(int(index))
        if plot is None:
            return None
        for val in plot['data']['traces']:
            if val['name'] == channelName:
                return val
        return val


class PowerFlowResult(Result):
    """
        潮流结果处理类，继承 Result， 

        提供快速获取 buses 和 branches 的接口，并提供潮流写入项目的接口

        该类只提供潮流仿真时使用

    """
    def __init__(self, *args, **kwargs):
        """
            初始化
        """
        Result.__init__(self, *args, **kwargs)

    def getBuses(self):
        """
            获取潮流结果 buses 数据

            >>> channel= result.getBuses()
            [...]
        """

        result = []
        pattern = re.compile("value=\"(.*)\"")
        data = self.db.getMessagesByKey('buses-table')
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

            >>> channel= result.getBranches()
            [...]
        """

        result = []
        pattern = re.compile("value=\"(.*)\"")
        data = self.db.getMessagesByKey('branches-table')
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

            >>> channel= result.powerFlowModify(model)
        """

        data = self.db.getMessagesByKey('power-flow-modify')
        if len(data) == 0:
            raise Exception('未找到到数据')
        self.modify(data[0], model)


class IESResult(Result):
    """
        综合能源结果处理类，继承 Result， 

        提供快捷 plot 数据的接口函数，获取到的 plot 数据为合并后的数据格式，不在是接收时分段的数据

        该类只提供 IES 仿真使用

    """
    def __init__(self, *args, **kwargs):
        """
            初始化
        """
        Result.__init__(self, *args, **kwargs)
        self.result = {'Sankey': []}
        self.__plotIndex = 0

    def __readPlotResult(self):
        length = self.db.getMessageLength()
        if (length > self.__plotIndex):
            for num in range(self.__plotIndex, length):
                val = self.db.getMessage(num)
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
            self.__plotIndex = length

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

class IESLabSimulationResult(IESResult):
    pass

class IESLabTypicalDayResult(IESResult):
    def GetTypicalDayNum():
        '''
            获取当前result的典型日数量
            
            :return: int类型，代表典型日数量
        '''
    def GetTypicalDayInfo(dayID):
        '''
            获取dayID对应典型日的基础信息
            
            :params: dayID int类型，表示典型日的ID，数值位于 0~典型日数量 之间
            
            :return: dict类型，代表典型日的基础信息，包括典型日所代表的日期范围、典型日的名称等
        '''
    def GetTypicalDayCurve(dayID, dataType):
        '''
            获取dayID对应典型日下dataType参数的时序曲线
            
            :params: dayID int类型，表示典型日的ID，数值位于 0~典型日数量 之间
            :params: dataType enum类型，标识辐照强度、环境温度、土壤温度、建筑物高度风速、风机高度风速、电负荷、热负荷、冷负荷的参数类型
            
            :return: list<float>类型，代表以1h为时间间隔的该参数的日内时序曲线
        '''
    pass
