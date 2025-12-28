import copy
import uuid
from deprecated import deprecated
from .result import Result


class VirtualInput:
    """
        虚拟输入类，用于仿真结果的输入

        该类只提供 EMT 仿真使用
    """

    def __init__(self,**kwargs):
        self.args=kwargs

    def toJson(self):
        """
            转换为 json 数据
        """
        return {
            "type": 'virtual_input',
            "data": self.args,
        }
    
    def update(self,**kwargs):
        """
            更新输入参数
        """
        for key,value in kwargs.items():
            self.args[key]=value
class EMTResult(Result):
    """
        电磁暂态结果视图， 

        提供快捷 plot 数据的接口函数，获取到的 plot 数据为合并后的数据格式，不在是接收时分段的数据

        该类只提供 EMT 仿真使用

    """
    
    def __init__(self,job, receiver, sender = None):
        super().__init__(job, receiver, sender)
        self.virtualInput=VirtualInput()
    
    __messageIndex = 0
    def getPlots(self):
        '''
            获取所有的 plots 数据

            >>> result.getPlots()
            {...}
        '''
        maxLength = len(self._receiver.messages)
        for i in range(self.__messageIndex,maxLength):
            val = self._receiver.messages[i]
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
        self.__messageIndex = maxLength
        return self.result.values()
    
    def getPlot(self, index: int):
        '''
            获取指定序号的曲线分组

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
    
    def next(self):
        """
            前进一个时步
        """
        
        self.goto(-1)
        
    def goto(self,step):
        """
            前进到指定时步
        """
        if self._sender is not None:
            self._sender.write({'type': 'debug', 'step': step})
        else:
            raise Exception('sender is None')
    
    
    def writeShm(self,path,buffer,offset):
        """
            写内存接口 （未最终确定，后续版本进行修改，使用时注意版本）
        """
        if self._sender is not None:
            self._sender.write({'type': 'memory', 'path': path,'buffer':buffer,'offset':offset})
        else:
            raise Exception('transmitter is None')
        
    def send(self,message=None):
        """
            发送消息
        """
        if self._sender is not None:
            val ={
                "type": 'virtual_input',
                "data": message,
            } 
            if type(message) is VirtualInput:
                val = message.toJson()
            
            if message is  None:
                val = self.virtualInput.toJson()
            
            self._sender.write(val)
        else:
            raise Exception('transmitter is None')
        

    
    def _writeEvent(self,eventType,eventTime,eventTimeType,defaultApp):
        if self._sender is  None:
            raise Exception('transmitter is None')
        event = {
            'eventType': eventType,
            'eventTime': eventTime,
            'eventTimeType':eventTimeType,
            "defaultApp": defaultApp
        }
        self._sender.write({'type': 'eventchain', 'event': [event]})
    
    def stopSimulation(self):
        """
            停止仿真
        """
        param = {
            "ctrl_type": "0",
            "uuid": str(uuid.uuid1()),
            'message': {
                'log': '停止任务 ',
            }
        }
        eventData = {}
        eventData = {'SimuCtrl': param}

        self._writeEvent('time','-1','1',{'SimuCtrl': eventData})
            
    def _snapshotControl(self,ctrlType,snapshotNumber,log):
        """
            断面控制
        """
        param = {
            "ctrl_type": ctrlType,
            "snapshot_number": snapshotNumber,
            "uuid": str(uuid.uuid1()),
            'message': {
                'log': log
            },
        }
        eventData = {}
        eventData = {'SnapshotCtrl': param}
        self._writeEvent('time','-1','1',{'SnapshotCtrl': eventData})  
    def saveSnapshot(self,snapshotNumber,log='保存断面成功'):
        """
            通过事件链保存断面
        """
        self._snapshotControl('0',snapshotNumber,log)
    def loadSnapshot(self,snapshotNumber,log='加载断面成功'):
        """
            通过事件链加载断面
        """
        self._snapshotControl('1',snapshotNumber,log)
        
    def control(self,controlParam,eventTime='-1',eventTimeType='1'):
        """
            控制仿真
        """    

        if type(controlParam) is not list:
            controlParam=[controlParam]
        para={}
        
        for param in controlParam:
            para[param['key']]={
                'Value': {
                    'value': param['value'],
                    'uuid': param['uuid'] if param.get('uuid',None) is not None else str(uuid.uuid1()),
                    'cmd': 'add',
                    'message': param.get('message')  if param.get('message',None) is not None else{
                        'log': param.get('log')  if param.get('log',None) is not None else '值变化到 '+str(param['value']),
                    },
                }
            }
        self._writeEvent('time',eventTime,eventTimeType,{'para': para})
        pass
    
    def monitor(self,monitorParam,eventTime='-1',eventTimeType='1'):
        
        if type(monitorParam) is not list:
            monitorParam=[monitorParam]
        para={}
        for param in monitorParam:
            para[param['key']]={
                'a': {
                    'uuid':param['uuid'] if param.get('uuid',None) is not None else str(uuid.uuid1()),
                    'function':param['function'],
                    'cmd':'add',
                    'period':param['period'],
                    'value':param['value'],
                    'key':param['key'],
                    'freq':param['freq'],
                    'condition':param['condition'],
                    'cycle':param['cycle'],
                    'nCount':param['nCount'],
                    'message': param.get('message')  if param.get('message',None) is not None else{
                        'log': param.get('log')  if param.get('log',None) is not None else '消息达到阈值 '+str(param['value']),
                    },
                }
            }
        self._writeEvent('time',eventTime,eventTimeType,{'para': para})
        
        pass