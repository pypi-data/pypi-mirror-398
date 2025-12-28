from cloudpss.runner.IESLabPlanResult import IESLabPlanResult, IESLabOptResult
from cloudpss.runner.runner import HttpRunner, HttpOPTRunner
from cloudpss.model import Model
from cloudpss.model.revision import ModelRevision
from ..utils import request
import json
from enum import IntEnum


class IESLabPlanModel(object):
    _baseUri = 'api/ieslab-plan/rest'
    _runUri = 'api/ieslab-plan/taskmanager'

    def __init__(self, simulationId):
        '''
            初始化
        '''
        self.simulationId = simulationId
        self.optimizationInfo = self.GetOptimizationInfo()

    def _fetchItemData(self, url, params):
        '''
            获取当前算例的优化目标设置信息

            :return: List 类型，包括优化目标和全局参数储能动作灵敏度，若没有设置则返回 []
        '''
        r = request('GET', url, params=params)
        data = json.loads(r.text)
        return data['results']

  
    def GetOptimizationInfo(self):
        '''
            获取当前算例的优化目标设置信息

            :return: enum 类型，代表经济性优化和环保性优化的类型
        '''
        try:
            data = self._fetchItemData(self._baseUri)
            for e in OptimizationMode:
                if (e.value == data['data']['optimizationpara']
                    ['OptimizationMode']):
                    return e
        except:
            return OptimizationMode['经济性']

    def SetOptimizationInfo(self, optType):
        '''
            无对应接口
            设置当前算例的优化目标

            :param optType: enum 类型，代表经济性优化和环保性优化的类型
        '''
        self.optimizationInfo = optType
        return True
    
    def run(self) -> HttpRunner[IESLabPlanResult]:
        '''
            生成方案优选算例

            :return: Runner[IESLabPlanResult]
        '''
        isRunning = self.GetLastTaskResult()
        if isRunning:
            raise Exception('该算例正在运行！请从浏览器算例页面点击结束运行或者调用IESPlan对象的kill接口终止计算后重试！')
        else:
            url = f'{self._runUri}/runOptimization'
            optType = self.optimizationInfo if self.optimizationInfo is not None else OptimizationMode.经济性
            optTypeValue = optType.value if isinstance(optType, OptimizationMode) else 0
            try:
                r = request('GET',
                            url,
                            params={
                                "simuid":
                                self.simulationId,
                                "optPara":
                                json.dumps({
                                    "OptimizationMode": optTypeValue,
                                    "ProjectPeriod": "20"
                                })
                            })
                data = json.loads(r.text)
                return HttpRunner({}, self.simulationId)
            except:
                raise Exception('生成方案优选算例失败')

    def GetRunner(self) -> HttpRunner[IESLabPlanResult]:
        '''
            获得运行实例

            :return: Runner[IESLabPlanResult]
        '''
        return HttpRunner({}, self.simulationId)
    
    def kill(self) -> bool:
        '''
            停止并删除当前运行的优化算例
        '''
        res = IESLabPlanResult(self.simulationId).getLastTaskResult()
        error = res.get('error', 0)
        if error == 0:
            data = res.get('data', {})
            if data is not None:
                taskID = data.get('task_id', '')
        url = f'{self._runUri}/removeOptimizationTask'
        try:
            r = request('GET',
                        url,
                        params={
                            "taskid": taskID,
                            "stopFlag": '2'
                        })
            json.loads(r.text)
            return True
        except:
            return False

    def GetLastTaskResult(self)-> bool:
        '''
            获取最后一次运行的taskID的运行结果与日志

            :return: boolean 类型
        '''
        isRunning = True
        res = IESLabPlanResult(self.simulationId).getLastTaskResult()
        error = res.get('error', 0)
        if error == 0:
            data = res.get('data', {})
            if data is not None:
                status = data.get('status', '')
                if status == 'stop':
                    isRunning = False
        try:
            
            logs = IESLabPlanResult(self.simulationId).GetLogs()
            if logs is not None:
                for log in logs:
                    if(log.get('data', '') == 'run ends'):
                        isRunning = False
                        break
        except:
            return False
        return isRunning

  
class IESLabOptModel(object):
    _baseUri = 'api/ieslab-opt/rest'
    _runUri = 'api/ieslab-opt/taskmanager'


    def __init__(self, simulationId, rid):
        '''
            初始化
        '''
        self.simulationId = simulationId
        self.rid = rid
        self.optimizationInfo = self.GetOptimizationInfo()

    def _fetchItemData(self, url, params):
        '''
            获取当前算例的优化目标设置信息

            :return: List 类型，包括优化目标和全局参数储能动作灵敏度，若没有设置则返回 []
        '''
        r = request('GET', url, params=params)
        data = json.loads(r.text)
        return data['results']

    def GetOptimizationInfo(self):
        '''
            获取当前算例的优化目标设置信息

            :return: Dict 类型，例如：{'OptGoal': <OptimizationMode.经济性: 0>, 'StoSen': "10", '@debug': '', 'clustering_algorithm': '0', 'num_method': '0', AbandonRen: '0', 'PowUnPrice': '1000', 'HeatAbandonPrice': '1000'}
        '''
        try:
            url = f'{self._baseUri}/simuOpt/'
            params = {"simu_id": self.simulationId}
            r = self._fetchItemData(url, params)
            if (len(r) == 0): 
                return {
                    "OptGoal": OptimizationMode['经济性'],
                    "StoSen": "10",
                    "@debug": "",
                    "clustering_algorithm": "0",
                    "num_method": "0",
                    "AbandonRen": "0",
                    "PowUnPrice": "1000",
                    "HeatAbandonPrice": "1000"
                }
            else:
                value = json.loads(r[0]['opt_params'])
                return {
                    "OptGoal": OptimizationMode(int(value.get('OptGoal', 0))),
                    "StoSen": value.get("StoSen", "10"),
                    "@debug": value.get("@debug", ""),
                    "clustering_algorithm": value.get("clustering_algorithm", "0"),
                    "num_method": value.get("num_method", "0"),
                    "AbandonRen": value.get("AbandonRen", "0"),
                    "PowUnPrice": value.get("PowUnPrice", "1000"),
                    "HeatAbandonPrice": value.get("HeatAbandonPrice", "1000")
                }
        except Exception as e:
            raise Exception(f"获取优化目标设置失败: {e}")

    def SetOptimizationInfo(self, data: dict):
        '''
            设置当前算例的优化目标

            :param data: dict 类型，例如：{'OptGoal': <OptimizationMode.经济性: 0>, 'StoSen': "10", '@debug': '', 'clustering_algorithm': '0', 'num_method': '0','AbandonRen': '0', 'PowUnPrice': '1000', 'HeatAbandonPrice': '1000'}

            :return: boolean 类型，为 True 则设置成功
        '''
        try:
            url = f'{self._baseUri}/simuOpt/'
            params = {"simu_id": self.simulationId}
            r = self._fetchItemData(url, params)
            opt_params = {
                "OptGoal": data.get('OptGoal', 0),
                "StoSen": data.get('StoSen', '10'),
                "@debug": data.get('@debug', ''),
                "clustering_algorithm": data.get('clustering_algorithm', '0'),
                "num_method": data.get('num_method', '0'),
                "AbandonRen": data.get('AbandonRen', '0'),
                "PowUnPrice": data.get('PowUnPrice', '1000'),
                "HeatAbandonPrice": data.get('HeatAbandonPrice', '1000')
            }
            if(len(r) == 0):
                payload = {
                    "simu_id": self.simulationId,
                    "opt_params": json.dumps(opt_params)
                }
                r = request('POST',
                            url,
                            data=json.dumps(payload))
                return True
            else:
                url2 = f'{self._baseUri}/simuOpt/{r[0]["id"]}/'
                payload = {
                    "simu_id": self.simulationId,
                    "opt_params": json.dumps(opt_params),
                    "id": r[0]["id"]
                }
                r = request('PUT',
                            url2,
                            data=json.dumps(payload))
                return True
        except:
            return False
    
    def run(self) -> HttpOPTRunner[IESLabOptResult]:
        '''
            生成方案优选算例

            :return: Runner[IESLabOptResult]
        '''
        isRunning = self.GetLastTaskResult()
        if isRunning:
            raise Exception('该算例正在运行！请从浏览器算例页面点击结束运行或者调用IESPlan对象的kill接口终止计算后重试！')
        else:
            # 通过 rid 获取 model
            model = Model.fetch(self.rid)
            # 通过 model 获取 revision
            revision = ModelRevision.create(model.revision, model.revision.hash)
            hash = revision.get('hash', '')
            url = f'{self._runUri}/runOptimization'
            opt = {
                "OptGoal": self.optimizationInfo.get('OptGoal', 0).value,
                "StoSen": self.optimizationInfo.get('StoSen', 10),
                "@debug": self.optimizationInfo.get('@debug', ''),
                "clustering_algorithm": self.optimizationInfo.get('clustering_algorithm', '0'),
                "num_method": self.optimizationInfo.get('num_method', '0'),
                "AbandonRen": self.optimizationInfo.get('AbandonRen', '0'),
                "PowUnPrice": self.optimizationInfo.get('PowUnPrice', '1000'),
                "HeatAbandonPrice": self.optimizationInfo.get('HeatAbandonPrice', '1000'),
            }
            try:
                r = request('GET',
                            url,
                            params={
                                "simuid":
                                self.simulationId,
                                "optPara":
                                json.dumps(opt),
                                "revision": hash
                            })
                data = json.loads(r.text)
                return HttpOPTRunner({}, self.simulationId)
            except:
                raise Exception('生成方案优选算例失败')

    def GetRunner(self) -> HttpOPTRunner[IESLabOptResult]:
        '''
            获得运行实例

            :return: Runner[IESLabOptResult]
        '''
        return HttpOPTRunner({}, self.simulationId)
    
    def kill(self) -> bool:
        '''
            停止并删除当前运行的优化算例
        '''
        res = IESLabOptResult(self.simulationId).getLastTaskResult()
        error = res.get('error', 0)
        if error == 0:
            data = res.get('data', {})
            if data is not None:
                taskID = data.get('task_id', '')
        url = f'{self._runUri}/removeOptimizationTask'
        try:
            r = request('GET',
                        url,
                        params={
                            "taskid": taskID,
                            "stopFlag": '2'
                        })
            json.loads(r.text)
            return True
        except:
            return False

    def GetLastTaskResult(self)-> bool:
        '''
            获取最后一次运行的taskID的运行结果与日志

            :return: boolean 类型
        '''
        isRunning = True
        res = IESLabOptResult(self.simulationId).getLastTaskResult()
        error = res.get('error', 0)
        if error == 0:
            data = res.get('data', {})
            if data is not None:
                status = data.get('status', '')
                if status == 'stop':
                    isRunning = False
        logs = IESLabOptResult(self.simulationId).GetLogs()
        if logs is not None:
            for log in logs:
                if(log.get('data', '') == 'run ends'):
                    isRunning = False
                    break
        return isRunning



# @unique
class OptimizationMode(IntEnum):
    经济性 = 0
    环保性 = 1