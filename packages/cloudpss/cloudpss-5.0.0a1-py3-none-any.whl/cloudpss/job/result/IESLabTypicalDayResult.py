from .IESResult import IESResult
import re
import copy
from cloudpss.job.messageStreamReceiver import MessageStreamReceiver, Message
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading
import time
from queue import Queue

class IESLabTypicalDaySubMessageResult():
    def __init__(self, output) -> None:
        self.receiver = MessageStreamReceiver(output)
        # self.result={}
    
    def connect(self):
        self.receiver.connect()
    
    def status(self):
        return self.receiver.status()
    
    def wait(self,timeout=10,current_time=None):
        start = time.time()
        while True:
            time.sleep(0.1)
            if self.receiver.isEnd(current_time):
                break
            if time.time()-start>timeout:
                break
                # raise Exception("获取数据超时")
    
    def getMessages(self,timeout=10,current_time=None):
        result={}
        self.wait(timeout,current_time)
        
        for val in self.receiver:
            if val.get('type',None) !='plot':
                continue
            result[val['key']] = val['data']
        return result

class IESLabTypicalDayResult(IESResult):
    
    def __init__(self, *args, **kwargs):
        """
            初始化
        """
        IESResult.__init__(self, *args, **kwargs)
        self.__plotIndex = 0
        self.__typicalIndex = 0
        self.__type_list =['总辐射','散射辐射', '直射辐射','天顶角', '环境温度', '湿球温度','土壤温度', '10m风速', '50m风速','电负荷', '热负荷','冷负荷','氢负荷']
        self.__map_load = { 'maxElectricalLoad':'电负荷', 'maxHeatLoad':'热负荷','maxCoolLoad':'冷负荷','maxHydrogenLoad':'氢负荷' }
        self.token = ''
        
        self.result = {'TypicalMonth': [{'月份': int,'持续天数': [],**{key: [] for key in self.__type_list}} for i in range(12)],'TypicalDay': []}
        self.messagemap={}

    def __readPlotResult(self):

        length = self.getMessageLength()

        print(length)
        if (length > self.__plotIndex):
            

                # stream_id = "fce32578-75c2-4aca-8323-1ce60941e57b"

                # if val['type'] == 'plot':# 每个月各类型数据的各个典型日的数据，由于部分月份可能没有电冷热负荷，某月的某个典型日可能缺少冷热负荷
                #     key_re = re.split('-month',val['key'])#格式为：散射辐射-month1，re后分别为类型和月份
                #     typical_month_m = self.result['TypicalMonth'][int(key_re[1])-1]
                #     typical_month_m['月份'] = int(key_re[1])
                #     val_data_traces = val['data']['traces']
                #     #val['data']['traces'][i]['name']格式为：典型日1-共31天，re正则后[0]为典型日顺序，[1]为持续天数
                #     typicalNum = int(re.findall('\d+',val_data_traces[-1]['name'])[0])
                #     for i in range(typicalNum):#取该类型的最后一个典型日顺序，当该类型缺少后排典型日时，小于实际典型日数量
                #         typical_month_m[key_re[0]].append([])
                #         if key_re[0]  == '环境温度':#各类版本气象数据均有环境温度数据，其典型日数量为实际数量
                #             typical_month_m['持续天数'].append(int(re.findall('\d+',val_data_traces[i]['name'])[1]))
                #     # 当前排典型日缺少数据时，该类型数据为空list[]；当后排典型日缺少数据时，该类型数据为空
                #     for i in range(len(val_data_traces)):
                #         typical_month_m[key_re[0]][int(re.findall('\d+',val_data_traces[i]['name'])[0])-1] = copy.deepcopy(val_data_traces[i]['y']) 

            self.__plotIndex = length
            # update TypicalDay based on TypicalMonth
            for m in range(12):
                typical_month_m = self.result['TypicalMonth'][m]
                typical_month_m_day = len(typical_month_m['持续天数'])
                for i in range(typical_month_m_day):
                    self.result['TypicalDay'].append({'info':{'typicalDayID': int, 'name': str, 'duration': int, **{key: 0.0 for key in self.__map_load}},
                    'data': {**{key: [] for key in self.__type_list}}})
                    typical_day_index = self.result['TypicalDay'][self.__typicalIndex]
                    typical_day_index['info']['typicalDayID'] = self.__typicalIndex
                    typical_day_index['info']['name'] = str(m+1) + '月典型日' + str(i+1)
                    typical_day_index['info']['duration'] = typical_month_m['持续天数'][i]
                    for key,value in self.__map_load.items():
                        # 分别处理该典型日无此类型负荷数据，缺少后序典型日，缺少前序典型日的情况
                        if typical_month_m.get(value) and i <len(typical_month_m[value]) and len(typical_month_m[value][i]):
                            typical_day_index['info'][key] = max(typical_month_m[value][i])
                    for type_i in self.__type_list:
                        # 某月冷热负荷可能缺少后续典型日数据
                        if typical_month_m[type_i] and i < len(typical_month_m[type_i]):
                            typical_day_index['data'][type_i] = typical_month_m[type_i][i]
                    self.__typicalIndex += 1
    def __init_message_map(self):      
        
        message = self.getMessagesByKey("message_map")
        if message is None or len(message) == 0:
            return
        
        self.messagemap = {}
        for m in message:
            dataMap = m['data']['map']
            for item in dataMap:
                messages = item['messages']
                for val in messages:
                    self.messagemap[val] = item['id']
                    
    def __init_result(self):
        self.__init_message_map()
        # print(self.messagemap)
        current_time = time.time()
        
        for key,val in self.messagemap.items():
            
            sub=IESLabTypicalDaySubMessageResult(val)
            sub.connect()
            message = sub.getMessages(current_time=current_time,timeout=10)
            print("key",key,'message', message)
        
        
        pass
        
    
    def GetTypical(self):
        '''
            获取所有的 GetTypical 典型日数据

            >>> result.GetTypical()
            {...}
        '''
        self.__init_result()
        return self.result['TypicalDay']
    def GetTypicalDayNum(self):
        '''
            获取当前result的典型日数量
            
            :return: int类型，代表典型日数量
        '''
        
        self.__readPlotResult()
        return self.__typicalIndex
    def GetTypicalDayInfo(self,dayID):
        '''
            获取dayID对应典型日的基础信息
            
            :params: dayID int类型，表示典型日的ID，数值位于 0~典型日数量 之间
            
            :return: dict类型，代表典型日的基础信息，包括典型日所代表的日期范围、典型日的名称等
        '''
        self.__readPlotResult()
        return self.result['TypicalDay'][dayID].get('info','没有该数据')
        
    def GetTypicalDayCurve(self,dayID, dataType):
        '''
            获取dayID对应典型日下dataType参数的时序曲线
            
            :params: dayID int类型，表示典型日的ID，数值位于 0~典型日数量 之间
            :params: dataType enum类型，标识辐照强度、环境温度、土壤温度、建筑物高度风速、风机高度风速、电负荷、热负荷、冷负荷的参数类型
            
            :return: list<float>类型，代表以1h为时间间隔的该参数的日内时序曲线
        '''
        self.__readPlotResult()
        return self.result['TypicalDay'][dayID]['data'].get(dataType,'没有该类型数据')
    
    def GetTypicalMonth(self):
        '''
            获取所有的 GetTypicalMonth 数据
            
            >>> result.GetTypicalMonth()
            
            :return: list<dict>类型，代表各月各类型的典型日数据
        '''
        self.__readPlotResult()
        return self.result['TypicalMonth']
    
    def GetTypicalMonthNum(self,monthID):
        '''
            获取第monthID月各类型的典型日数据

            >>> result.GetTypicalMonthNum()
            
            :params: monthID int类型，表示典型月的ID，数值位于 1-12 之间

            :return: dict类型，代表第monthID月各类型的典型日数据
            {...}
        '''
        self.__readPlotResult()
        return self.result['TypicalMonth'][monthID-1]
        
    
    def GetTypicalMonthCurve(self,monthID, dataType):
        '''
            获取dayID对应典型日下dataType参数的时序曲线
            
            :params: monthID int类型，表示典型月的ID，数值位于 1-12 之间
            :params: dataType enum类型，标识总辐射、环境温度、土壤温度、建筑物高度风速、风机高度风速、电负荷、热负荷、冷负荷的参数类型
            
            :return: list<list>类型，代表以1h为时间间隔的该参数的典型日内时序曲线
        '''
        self.__readPlotResult()
        return self.result['TypicalMonth'][monthID-1].get(dataType,'没有该类型数据')
    

    
 


