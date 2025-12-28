from .result import Result
import re
import copy
class IESLabTypicalDayResult(Result):
    def __init__(self, *args, **kwargs):
        """
            初始化
        """
        Result.__init__(self, *args, **kwargs)
        self.__plotIndex = 0
        self.__typicalIndex = 0
        self.__type_list =['总辐射','散射辐射', '直射辐射','天顶角', '环境温度', '湿球温度','土壤温度', '10m风速', '50m风速','电负荷', '热负荷','冷负荷','氢负荷']
        self.__map_load = { 'maxElectricalLoad':'电负荷', 'maxHeatLoad':'热负荷','maxCoolLoad':'冷负荷','maxHydrogenLoad':'氢负荷' }
        self.result = {'TypicalMonth': [{'月份': int,'持续天数': [],**{key: [] for key in self.__type_list}} for i in range(12)],'TypicalDay': []}

    def __readPlotResult(self):
        length = self.db.getMessageLength()
        if (length > self.__plotIndex):
            for num in range(self.__plotIndex, length):# update TypicalMonth
                val = self.db.getMessage(num)
                if val['type'] == 'plot':# 每个月各类型数据的各个典型日的数据，由于部分月份可能没有电冷热负荷，某月的某个典型日可能缺少冷热负荷
                    key_re = re.split('-month',val['key'])#格式为：散射辐射-month1，re后分别为类型和月份
                    typical_month_m = self.result['TypicalMonth'][int(key_re[1])-1]
                    typical_month_m['月份'] = int(key_re[1])
                    val_data_traces = val['data']['traces']
                    #val['data']['traces'][i]['name']格式为：典型日1-共31天，re正则后[0]为典型日顺序，[1]为持续天数
                    typicalNum = int(re.findall('\d+',val_data_traces[-1]['name'])[0])
                    for i in range(typicalNum):#取该类型的最后一个典型日顺序，当该类型缺少后排典型日时，小于实际典型日数量
                        typical_month_m[key_re[0]].append([])
                        if key_re[0]  == '环境温度':#各类版本气象数据均有环境温度数据，其典型日数量为实际数量
                            typical_month_m['持续天数'].append(int(re.findall('\d+',val_data_traces[i]['name'])[1]))
                    # 当前排典型日缺少数据时，该类型数据为空list[]；当后排典型日缺少数据时，该类型数据为空
                    for i in range(len(val_data_traces)):
                        typical_month_m[key_re[0]][int(re.findall('\d+',val_data_traces[i]['name'])[0])-1] = copy.deepcopy(val_data_traces[i]['y'])            
            
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
            self.__plotIndex = length
            
    def GetTypical(self):
        '''
            获取所有的 GetTypical 典型日数据

            >>> result.GetTypical()
            {...}
        '''
        self.__readPlotResult()
        return self.result['TypicalDay']
        

    def GetTypicalDayNum(self):
        '''
            获取当前result的典型日总数
            
            :return: int类型，代表典型日数量
        '''
        self.__readPlotResult()
        return self.__typicalIndex
        
    def GetTypicalDayInfo(self,dayID):
        '''
            获取dayID对应典型日的基础信息
            
            :params: dayID int类型，表示典型日的ID，数值位于 [0，典型日总数-1] 中
            
            :return: dict类型，代表典型日的基础信息，包括典型日所代表的日期范围、典型日的名称等
        '''
        self.__readPlotResult()
        try:
            return self.result['TypicalDay'][dayID]['info']
        except:
            raise Exception('未查询到该数据')
        

    def GetTypicalDayCurve(self,dayID, dataType):
        '''
            获取dayID对应典型日下dataType参数的时序曲线
            
            :params: dayID int类型，表示典型日的ID，数值位于 [0，典型日总数-1] 中
            :params: dataType enum类型，标识典型场景的数据类型
            有总辐射、直射辐照、散射辐照、环境温度、湿球温度、土壤温度、10m风速、50m风速、电负荷、热负荷、冷负荷和氢负荷等类型，以该典型场景实际包含的类型为准
            
            :return: list<float>类型，代表以1h为时间间隔的该参数的日内时序曲线
        '''
        self.__readPlotResult()
        try:
            return self.result['TypicalDay'][dayID]['data'][dataType]
        except:
            raise Exception('未查询到该数据')
        
        
        
    def GetTypicalMonth(self):
        '''
            获取所有的 GetTypicalMonth 数据
            
            >>> result.GetTypicalMonth()
            
            :return: list<dict>类型，代表各月各类型的典型日数据
        '''
        self.__readPlotResult()
        return self.result['TypicalMonth']
    
    def GetTypicalMonthID(self,monthID):
        '''
            获取第monthID月各类型的典型日数据

            >>> result.GetTypicalMonthID()
            
            :params: monthID int类型，表示典型月的ID，数值位于 1-12 之间

            :return: dict类型，代表第monthID月各类型的典型日数据
            {...}
        '''
        self.__readPlotResult()
        try:
            return self.result['TypicalMonth'][monthID-1]
        except:
            raise Exception('未查询到该数据')
        
    
    def GetTypicalMonthCurve(self,monthID, dataType):
        '''
            获取monthID对应典型日下dataType参数的时序曲线
            
            :params: monthID int类型，表示典型月的ID，数值位于 1-12 之间
            :params: dataType enum类型，标识典型场景的数据类型
            有总辐射、直射辐照、散射辐照、环境温度、湿球温度、土壤温度、10m风速、50m风速、电负荷、热负荷、冷负荷和氢负荷等类型，以该典型场景实际包含的类型为准
            
            :return: list<list>类型，代表以1h为时间间隔的该参数的典型日内时序曲线
        '''
        self.__readPlotResult()
        try:
            return self.result['TypicalMonth'][monthID-1][dataType]
        except:
            raise Exception('未查询到该数据')        

