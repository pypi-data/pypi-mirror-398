import time
from cloudpss.runner.runner import Runner, HttpRunner, DSLabRunner
from cloudpss.runner.DSLabResult import DSLabResult
from ..utils import request
import json

class DSLabFinancialAnalysisModel(object):
    _baseUri = 'api/dslab/rest/pe/'

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
        r = request('POST', url, None, data=json.dumps(data))
        return json.loads(r.text)

    def _fetchItemData(self, url, planID):
        '''
            获取planID对应的优化方案下财务评估模块的基础信息
            :param planID int类型，表示优化方案的ID，数值位于0~优化方案数量之间

            :return: dict 类型，为源数据的引用，代表方案对应的财务评价基础参数信息
        '''
        r = request('GET',
                    url,
                    params={
                        "planId": planID,
                        "simu": self.simulationId
                    })
        return json.loads(r.text)
    
    def run(self, planID) -> Runner[DSLabResult]:
        '''
            运行财务评价概览计算

            :param planID int类型，表示优化方案的ID，数值位于0~优化方案数量之间

            :return: Runner[DSLabResult]
        '''
        url = 'api/dslab/rest/saveDataToclickhouse'
        try:
            r = request('GET',
                        url,
                        params={
                            "planId": planID,
                            "simu": self.simulationId,
                            "CMD_TYPE": 'financialEvaluation'
                        })
            data = json.loads(r.text)
            return DSLabRunner({'rid': 'function/ieslab/evaluation'},
                self.simulationId,
                planId=planID,
                cmdType='financialEvaluation')
        except:
            raise Exception('财务评价概览计算失败')

    def GetFinancialParams(self, planID):
        '''
            获取planID对应的优化方案下财务评估模块的基础信息
            :param planID int类型，表示优化方案的ID，数值位于0~优化方案数量之间

            :return: dict 类型，为源数据的引用，代表方案对应的财务评价基础参数信息
        '''
        dict_result = dict()
        for k, v in self._kindNameMap.items():
            kind = self._kindNameMap.get(k, k)
            url = f"{self._baseUri}{kind}"
            list_data  = self._fetchItemData(url, planID)
            if not list_data :
                data = {
                    "simu": self.simulationId,
                    "planId": planID,
                }
                if k in self._financialParasDefaultValues:
                    data.update(self._financialParasDefaultValues[k])
                    dict_result[v]  = self._saveItemData(url, data)
            else:
                dict_result[v] = list_data
        return dict_result
