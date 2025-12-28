import json
from ..utils import request
from ..model.model import Model
from .dataManageModel import DSLabDataManageModel
from .financialAnalysisModel import DSLabFinancialAnalysisModel
from cloudpss.runner.DSLabResult import DSLabResult
from cloudpss.runner.runner import Runner
from cloudpss.runner.result import IESResult, EMTResult

class DSLab(object):
    def __init__(self, project={}):
        '''
            初始化
        '''
        self.id = project.get('id', None)
        self.resource = project.get('resource', None)
        self.name = project.get('name', None)
        self.__modelRid = project.get('model', None)
        if self.__modelRid is not None:
            self.model = Model.fetch(self.__modelRid)
        self.dataManageModel = DSLabDataManageModel(self.resource)
        self.financialAnalysisModel = DSLabFinancialAnalysisModel(self.resource)
        self.currentEvaluationResult = DSLabResult(self.resource)

    @staticmethod
    def fetch(simulationId):
        '''
            获取算例信息

            :params: simulationId string类型，代表数据项的算例id

            :return: DSLab
        '''
        try:
            r = request(
                'GET', 'api/dslab/rest/simulation/{0}'.format(simulationId))
            project = json.loads(r.text)
            return DSLab(project)
        except Exception as e:
            if 'Unauthorized' in str(e): 
                raise Exception('token 无效')
            else:
                raise Exception('未查询到当前算例')

    def run(self, job=None, name=None):
        '''
            调用仿真 

            :params job:  调用仿真时使用的计算方案，不指定将使用算例保存时选中的计算方案
            :params name:  任务名称，为空时使用项目的参数方案名称和计算方案名称

            :return: 返回一个运行实例
        '''
        if job is None:
            currentJob = self.model.context['currentJob']
            job = self.model.jobs[currentJob]

        job['args']['simulationId'] = self.resource
        return self.model.run(job, name=name)
    
    def dsLabRun(self):
        '''
            生成方案优选算例

            :return: 方案优选运行实例
        '''
    pass

    def dsLabFinancialRun(self, planID):
        '''
            运行技术经济分析
            :param planID int 类型，表示优化方案的ID，数值位于0~优化方案数量之间

            :return: 技术经济分析实例

        '''
        return self.financialAnalysisModel.run(planID)
    

    def runIESLoadPrediction(self,job=None,name=None, **kwargs)->Runner[IESResult]:
        '''
            运行 负荷预测方案 内核，如果当前 model 没有创建  Job 时报错，默认使用第一个计算方案，进行仿真。
            
            :param: job 计算方案名称，可选，字符串类型或者字典类型,默认使用第一个计算方案，如果同名使用最靠前一个
            :params name:  任务名称，为空时使用项目的参数方案名称和计算方案名称

            :return: runner Runner[IESResult]
        '''
        rid = 'function/CloudPSS/ieslab-load-prediction'
        if job is None:
            currentJob = self.model.context['currentJob']
            job = self.model.jobs[currentJob]
            if job['rid'] != rid:
                for j in self.model.jobs:
                    if j['rid'] == rid:
                        job = j
        if job is None:
            raise Exception("找不到负荷预测方案内核运行的计算方案")
        if job['rid'] != rid:
            raise Exception("不是负荷预测方案内核运行生成算法的计算方案")
        return self.run(job=job, name=name)
    
    def runIESPowerFlow(self,job=None,name=None, **kwargs)->Runner[IESResult]:
        '''
            运行 时序潮流方案 内核，如果当前 model 没有创建  Job 时报错，默认使用第一个计算方案，进行仿真。
            
            :param: job 计算方案名称，可选，字符串类型或者字典类型,默认使用第一个计算方案，如果同名使用最靠前一个
            :params name:  任务名称，为空时使用项目的参数方案名称和计算方案名称

            :return: runner Runner[IESResult]
        '''
        rid = 'function/CloudPSS/ieslab-power-flow'
        if job is None:
            currentJob = self.model.context['currentJob']
            job = self.model.jobs[currentJob]
            if job['rid'] != rid:
                for j in self.model.jobs:
                    if j['rid'] == rid:
                        job = j
        if job is None:
            raise Exception("找不到时序潮流方案内核运行的计算方案")
        if job['rid'] != rid:
            raise Exception("不是时序潮流方案内核运行生成算法的计算方案")
        return self.run(job=job, name=name)

    def runIESEnergyStoragePlan(self,job=None,name=None, **kwargs)->Runner[IESResult]:
        '''
            运行 储能规划方案 内核，如果当前 model 没有创建  Job 时报错，默认使用第一个计算方案，进行仿真。
            
            :param: job 计算方案名称，可选，字符串类型或者字典类型,默认使用第一个计算方案，如果同名使用最靠前一个
            :params name:  任务名称，为空时使用项目的参数方案名称和计算方案名称

            :return: runner Runner[IESResult]
        '''
        rid = 'function/CloudPSS/ieslab-energy-storage-plan'
        if job is None:
            currentJob = self.model.context['currentJob']
            job = self.model.jobs[currentJob]
            if job['rid'] != rid:
                for j in self.model.jobs:
                    if j['rid'] == rid:
                        job = j
        if job is None:
            raise Exception("找不到储能规划方案内核运行的计算方案")
        if job['rid'] != rid:
            raise Exception("不是储能规划方案内核运行生成算法的计算方案")
        return self.run(job=job, name=name)

    def runIESShortCurrent(self,job=None,name=None, **kwargs)->Runner[IESResult]:
        '''
            运行 短路电流计算 内核，如果当前 model 没有创建  Job 时报错，默认使用第一个计算方案，进行仿真。
            
            :param: job 计算方案名称，可选，字符串类型或者字典类型,默认使用第一个计算方案，如果同名使用最靠前一个
            :params name:  任务名称，为空时使用项目的参数方案名称和计算方案名称

            :return: runner Runner[IESResult]
        '''
        rid = 'function/CloudPSS/short-circuit-current-calculation'
        if job is None:
            currentJob = self.model.context['currentJob']
            job = self.model.jobs[currentJob]
            if job['rid'] != rid:
                for j in self.model.jobs:
                    if j['rid'] == rid:
                        job = j
        if job is None:
            raise Exception("找不到短路电流计算方案内核运行的计算方案")
        if job['rid'] != rid:
            raise Exception("不是短路电流计算方案内核运行生成算法的计算方案")
        return self.run(job=job, name=name)
    
    @staticmethod
    def createProjectGroup(name, description=None, createById=None):
        '''
            创建项目组

            :params name: String 项目组名称 
            :params description: String 项目组描述 可选参数
            :params createById Int 父项目组id  可选参数，如果是从已有项目组导入的项目组，必填此项

            :return: Int 返回创建的项目组id
        '''
        try:
            if createById is None: 
                isImport = 0
            else:
                isImport = 1
            payload = {
                'name': name,
                'description': description,
                'isImport': isImport,
                'createById': createById,
            }
            r = request(
                'POST', 'api/dslab/rest/group', data=json.dumps(payload))
            if r.ok:
                r = request('GET', 'api/dslab/rest/group')
                groupList = json.loads(r.text)
                id = groupList[len(groupList) -1].get('id', None)
                return id
        except Exception as e:
            raise Exception('创建项目组失败')
        
    @staticmethod
    def createProject(name, gid, description=None, initialTerm=None, build=None, operate=None, yearsInOperation=None):
        '''
            创建项目

            :params name: String 项目名称 
            :params gid: Int 父项目组id,
            :params description: String 项目描述, 可选参数
            :params initialTerm: String 项目起始年限，可选参数
            :params build: String 项目建设期（年），可选参数
            :params operate: String 项目生命周期（年），可选参数
            :params yearsInOperation: String 已投运年限，可选参数

            :return: Int 返回创建的项目id
        '''
        try:
            payload = {
                'name': name,
                'gid': gid,
                'description': description,
                'config': {
                    'initialTerm': initialTerm,
                    'build': build,
                    'operate': operate,
                    'yearsInOperation': yearsInOperation,
                }
            }
            r = request(
                'POST', 'api/dslab/rest/simulation', data=json.dumps(payload))
            project = json.loads(r.text)
            return project.get('resource', None)
        except Exception as e:
            raise Exception('创建项目失败')
