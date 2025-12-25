import time
from cloudpss.runner.runner import HttpRunner, Runner, HttpOPTRunner
from cloudpss.runner.IESLabEvaluationResult import IESLabPlanEvaluationResult, IESLabOptEvaluationResult
from ..utils import request
import json
from enum import IntEnum, unique

class IESLabEvaluationModel(object):
    _baseUri = ''
    _taskUri = ''
    _runUri = ''
    _kindNameMap = {
        "投资组成": "investmentbanchandproportion",
        "资金来源": "capitalsource",
        "资产形式": "assetformation",
        "生产成本": "productioncost",
        "流动资金及财务费用": "workingcapitalandfinancialexpenses",
        "税率及附加": "projectcalculation",
    }

    # 财务评价基础参数接口默认值
    _financialParasDefaultValues = {
        "资产形式": {
            "fixedAssetsRatio": "95",
            "residualRrate": "5",
            "depreciationPeriod": "15",
            "reimbursementPeriod": "5"
        },
        "生产成本": {
            'annualSalary': "8",
            'capacity': "4",
            'insuranceRate': "0.25",
            'materialsExpenses': "5.0",
            'otherExpenses': "1.0",
            'welfareFactor': "0"
        },
        "流动资金及财务费用": {
            "annualAPCirculationTimes": "12",
            "annualARCirculationTimes": "12",
            "annualCashCirculationTimes": "12",
            "annualStockCirculationTimes": "12",
            "interestRateAndWorkingCapital": "4",
            "workingCapitalLoanRatio": "70"
        },
        "税率及附加": {
            "aleatoricAccumulationFundRate": "0",
            "basicDiscountRate": "8",
            "cityMaintenanceConstructionTaxTate": "5",
            "corporateIncomeTaxRate": "25",
            "educationFeePlus": "5",
            "electricityVATRate": "18",
            "fuelBoughtVATRate": "10",
            "hotColdVATRate": "12",
            "legalAccumulationFundRate": "10",
            "localEducationPlus": "2",
            "materialBoughtVATRate": "17",
            "steamSaleVATRate": "12"
        }
    }

    # 评价基础参数接口默认值
    _evaluationType = {
        "环保评价": "environmentalEvaluation",
        "能效评价": "energyEvaluation"
    }

    def __init__(self, simulationId):
        '''
            初始化
        '''
        self.simulationId = simulationId

    def _saveItemData(self, url, data):
        '''
            保存url链接对应的优化方案下财务评估模块的基础信息
            :param url string类型，表示优化方案的接口链接

            :return: dict 类型，代表方案对应的财务评价基础参数信息
        '''
        r = request('POST', url, data=json.dumps(data))
        dataList = json.loads(r.text)
        return dataList

    def _fetchItemData(self, url, planID):
        '''
            获取planID对应的优化方案下财务评估模块的基础信息
            :param planID int类型，表示优化方案的ID，数值位于0~优化方案数量之间

            :return: dict 类型，为源数据的引用，代表方案对应的财务评价基础参数信息
        '''
        r = request('GET',
                    url,
                    params={
                        "simu_id": self.simulationId,
                        "planId": planID,
                    })
        data = json.loads(r.text)
        return data

    def GetFinancialParams(self, planID):
        '''
            获取planID对应的优化方案下财务评估模块的基础信息
            :param planID int类型，表示优化方案的ID，数值位于0~优化方案数量之间

            :return: dict 类型，为源数据的引用，代表方案对应的财务评价基础参数信息
        '''
        dict_result = dict()
        for k, v in self._kindNameMap.items():
            kind = self._kindNameMap.get(k, k)
            url = self._baseUri + kind + '/'
            list = self._fetchItemData(url, planID)
            if (len(list['results']) == 0):
                data = {
                    "simu": self.simulationId,
                    "planId": planID,
                }
                if (k in self._financialParasDefaultValues):
                    data.update(self._financialParasDefaultValues[k])
                    res = self._saveItemData(url, data)
                    dict_result[v] = res
                else:
                    pass
            else:
                dict_result[v] = list['results']
        return dict_result

    def run(self, planID, type=None) -> HttpRunner[IESLabPlanEvaluationResult]:
        '''
            运行方案评估

            :param planID int类型，表示优化方案的ID，数值位于0~优化方案数量之间
            :params type:  string类型，任务类型：环保评价/能效评价

            :return: Runner[IESLabPlanEvaluationResult]
        '''
        url =  self._runUri
        CMD_TYPE = type if type is None else self._evaluationType[type]
        try:
            timeId = int(time.time() * 1000)
            r = request('GET',
                        url,
                        params={
                            "simuid": self.simulationId,
                            "planId": planID,
                            "CMD_TYPE": CMD_TYPE
                        })
            data = json.loads(r.text)
            return HttpRunner({'rid': 'function/ieslab/evaluation'},
                self.simulationId,
                timeId=timeId,
                planId=planID,
                cmdType=CMD_TYPE)
        except:
            raise Exception('方案评估开始计算失败')

    def EnvironmentalEvaluationRun(self, planID):
        '''
            运行环保评价方案评估

            :param planID int类型，表示优化方案的ID，数值位于0~优化方案数量之间

            :return: 方案评估运行实例
        '''
        return self.run(planID, 'environmentalEvaluation')

    def EnergyEvaluationRun(self, planID):
        '''
            运行能效评价方案评估

            :param planID int类型，表示优化方案的ID，数值位于0~优化方案数量之间

            :return: 方案评估运行实例
        '''
        return self.run(planID, 'energyEvaluation')

    def GetRunner(self, planID) -> Runner[IESLabPlanEvaluationResult]:
        '''
            获得运行实例

            :return: Runner[IESLabEvaluationResult]
        '''
        return HttpRunner({'rid': 'function/ieslab/evaluation'},
            self.simulationId,
            planId=planID)


@unique
class OptimizationMode(IntEnum):
    经济性 = 0
    环保性 = 1


class IESLabPlanEvaluationModel(IESLabEvaluationModel):
    _baseUri = 'api/ieslab-plan/rest/'
    _taskUri = 'api/ieslab-plan/taskmanager/getSimuLastTasks'
    _runUri = 'api/ieslab-plan/taskmanager/saveDataToclickhouse'

    def run(self, planID, type=None) -> HttpRunner[IESLabPlanEvaluationResult]:
        '''
            运行方案评估

            :param planID int类型，表示优化方案的ID，数值位于0~优化方案数量之间
            :params type:  string类型，任务类型：环保评价/能效评价

            :return: HttpRunner[IESLabEvaluationResult]
        '''
        url =  self._runUri
        CMD_TYPE = type if type is None else self._evaluationType[type]
        try:
            timeId = int(time.time() * 1000)
            r = request('GET',
                        url,
                        params={
                            "simuid": self.simulationId,
                            "planId": planID,
                            "CMD_TYPE": CMD_TYPE
                        })
            data = json.loads(r.text)
            return HttpRunner({'rid': 'function/ieslab/evaluation'},
                self.simulationId,
                timeId=timeId,
                planId=planID,
                cmdType=CMD_TYPE)
        except:
            raise Exception('方案评估开始计算失败')


class IESLabOptEvaluationModel(IESLabEvaluationModel):
    _baseUri = 'api/ieslab-opt/rest/'
    _taskUri = 'api/ieslab-opt/taskmanager/getSimuLastTasks'
    _runUri = 'api/ieslab-opt/taskmanager/saveDataToclickhouse'

    def run(self, planID, type=None) -> HttpOPTRunner[IESLabOptEvaluationResult]:
        '''
            运行方案评估

            :param planID int类型，表示优化方案的ID，数值位于0~优化方案数量之间
            :params type:  string类型，任务类型：环保评价/能效评价

            :return: HttpRunner[IESLabEvaluationResult]
        '''
        url =  self._runUri
        CMD_TYPE = type if type is None else self._evaluationType[type]
        try:
            timeId = int(time.time() * 1000)
            r = request('GET',
                        url,
                        params={
                            "simuid": self.simulationId,
                            "planId": planID,
                            "CMD_TYPE": CMD_TYPE
                        })
            data = json.loads(r.text)
            return HttpOPTRunner({'rid': 'function/ieslab/evaluation'},
                self.simulationId,
                timeId=timeId,
                planId=planID,
                cmdType=CMD_TYPE)
        except:
            raise Exception('方案评估开始计算失败')