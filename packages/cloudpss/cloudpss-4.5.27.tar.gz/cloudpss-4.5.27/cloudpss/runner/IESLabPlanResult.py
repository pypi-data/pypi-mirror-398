import json
from math import fabs
from ..utils.httprequests import request
# from .result import IESResult


class IESLabResult(object):
    _baseUri = ''
    taskId = None

    def __init__(self, simulationId, taskId=None) -> None:
        """
            初始化
            获得taskId
        """

        self.simulationId = simulationId
        if taskId is not None:
            self.taskId = taskId
        else:
            self.taskId = self.__getLastTask()

    def __getLastTask(self):
        '''
            获取最后一次运行的taskID

            :return: string 类型
        '''
        try:
            r=request('GET',f'{self._baseUri}/getSimuLastTasks',params={
                'simuid':self.simulationId
            })
            result= json.loads(r.text)
            return result['data'].get('task_id',None)
        except:
            return None

    def status(self):
        '''
            获取运行状态

            :return: boolean 类型
        '''
        log = self.GetLogs()
        for l in log:
            if l['data'] == 'run ends':
                return True
        return False

    def GetLogs(self):
        '''
            获取运行日志

            :return: dict 类型，代表日志信息
        '''
        if self.taskId is None:
            raise Exception('未开始运行')
            # return []
        r = request('GET',
                    f'{self._baseUri}/getOptimizationLog',
                    params={
                        'simuid': self.simulationId,
                        'taskid': self.taskId
                    })
        result = json.loads(r.text)
        return result['msg']

    def GetPlanNum(self):
        '''
            获取当前 result 实例对应的优化方案数量
            
            :return: int类型，代表优化方案的数量
        '''
        if self.taskId is None:
            raise Exception('未开始运行')
        r = request('GET',
                    f'{self._baseUri}/getOptimizationResult',
                    params={
                        'simuid': self.simulationId,
                        'taskid': self.taskId,
                        'resultType': 0
                    })
        result = json.loads(r.text)
        return len(result['data'])

    def GetPlanInfo(self, planID):
        '''
            获取planID对应的优化方案的基础信息
            
            :param: planID int 类型，表示优化方案的 ID，数值位于 0~优化方案数量 之间
            
            :return: dict 类型，代表该方案的基础信息，包括投资、运行成本、负荷总量等信息
        '''
        if self.taskId is None:
            raise Exception('未开始运行')
        length = self.GetPlanNum()
        if int(planID) > length:
            raise Exception('计算方案id未产生')
        r = request('GET',
                f'{self._baseUri}/getOptimizationResult',
                params={
                    'simuid': self.simulationId,
                    'taskid': self.taskId,
                    'resultType': 0
                })
        data = json.loads(r.text).get('data', [])
        filtered_data = [item for item in data if item['id'] == planID]
        if filtered_data:
            result = filtered_data[0].get('data', {}).get('data', [])[0]
            header = filtered_data[0].get('data', {}).get('headerDesc', [])
            dict_result = {val.get('hearderName', ''): result.get(val.get('key', ''), '') for val in header}
            return dict_result
        else:
            raise Exception('未查询到该方案id数据')


    def GetPlanConfiguration(self, planID):
        '''
            获取planID对应的优化方案的配置信息
            
            :param: planID int 类型，表示优化方案的ID，数值位于 0~优化方案数量 之间

            :return: dict 类型，代表该方案的配置信息，包括每种设备的选型配置、容量配置、成本等相关信息
        '''
        length = self.GetPlanNum()
        if int(planID) > length:
            raise Exception('计算方案id未产生')
        r = request('GET',
                    f'{self._baseUri}/getOptimizationResult',
                    params={
                        'simuid': self.simulationId,
                        'taskid': self.taskId,
                        "planId": planID,
                        'resultType': 1
                    })
        d = json.loads(r.text)
        if len(d['data']) == 0:
            raise Exception('未查询到该方案id数据')
        else: 
            result = {}
            for val in d['data']:
                result[val['u_name']] = val['data']['data']
            return result

    def GetComponentResult(self, planID, componentID, typicalDayName=''):
        '''
            获取planID对应的优化方案下componentID对应元件的运行信息
            
            :param: planID int 类型，表示优化方案的ID，数值位于 0~优化方案数量 之间
            :param: componentID str 类型，表示元件的标识符
            :param typicalDayName str 类型，代表典型日的名称

            :return: dict类型，代表该元件在不同典型日下的运行信息
        '''
        length = self.GetPlanNum()
        if int(planID) > length:
            raise Exception('计算方案id未产生')
        r = request('GET',
                    f'{self._baseUri}/getOptimizationResult',
                    params={
                        'simuid': self.simulationId,
                        'taskid': self.taskId,
                        'resultType': 3,
                        'typicalDay': typicalDayName,
                        "planId": planID,
                        'u_name': componentID
                    })
        d = json.loads(r.text)
        if len(d['data']) == 0:
            raise Exception('未查询到该方案id对应的优化方案下componentID对应元件数据')
        else:
            dict_result = dict()
            for val in d['data']:
                for k, v in val.items():
                    dict_result[k] = v
            return dict_result
    
    def GetEnergyBalanceResult(self, planID, typicalDayName=''):
        '''
            获取planID对应的优化方案下能量平衡图数据
            
            :param: planID int 类型，表示优化方案的ID，数值位于 0~优化方案数量 之间
            :param typicalDayName str 类型，代表典型日的名称

            :return: dict类型，代表该元件在不同典型日下的运行信息

        '''
        length = self.GetPlanNum()
        if int(planID) > length:
            raise Exception('计算方案id未产生')
        try:
            r = request('GET',
                        f'{self._baseUri}/getOptimizationResult',
                        params={
                            'simuid': self.simulationId,
                            'taskid': self.taskId,
                            'resultType': 4,
                            'typicalDay': typicalDayName,
                            "planId": planID,
                            "u_name": "systemData"
                        })
            return json.loads(r.text)
        except:
            raise Exception('运行失败')


    def GetComponentTypiDays(self, planID, componentID):
        '''
            获取当前result实例对应的优化方案数量

            :param: planID int 类型，表示优化方案的ID，数值位于 0~优化方案数量 之间
            :param: componentID str 类型，表示元件的标识符
            
            :return: int类型，代表优化方案的数量
        '''
        if self.taskId is None:
            raise Exception('未开始运行')
        length = self.GetPlanNum()
        if int(planID) > length:
            raise Exception('计算方案id未产生')
        r = request('GET',
                    f'{self._baseUri}/getOptimizationResult',
                    params={
                        'simuid': self.simulationId,
                        'taskid': self.taskId,
                        "planId": planID,
                        'u_name': componentID,
                        'resultType': 2
                    })
        result = json.loads(r.text)
        return result['data']
    
    def getLastTaskResult(self):
        '''
            获取最后一次运行的taskID的运行结果

            :return: dict 类型
        '''
        r=request('GET',f'{self._baseUri}/getSimuLastTasks',params={
            'simuid':self.simulationId
        })
        result= json.loads(r.text)
        return result


class IESLabPlanResult(IESLabResult):
    _baseUri = 'api/ieslab-plan/taskmanager'


class IESLabOptResult(IESLabResult):
    _baseUri = 'api/ieslab-opt/taskmanager'
    