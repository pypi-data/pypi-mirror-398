import json

from cloudpss.ieslab.DataManageModel import IESPlanDataManageModel
from cloudpss.ieslab.EvaluationModel import IESLabPlanEvaluationModel
from cloudpss.ieslab.PlanModel import IESLabPlanModel
from cloudpss.runner.IESLabTypicalDayResult import IESLabTypicalDayResult
from ..utils import request
from ..model.model import Model
from cloudpss.runner.runner import  Runner
from cloudpss.runner.IESLabPlanResult import IESLabPlanResult
from cloudpss.runner.IESLabEvaluationResult import IESLabPlanEvaluationResult

class IESLabPlan(object):
    def __init__(self, project={}):
        '''
            初始化
        '''
        self.id = project.get('id', None)
        self.name = project.get('name', None)
        self.__modelRid = project.get('model', None)
        self.project_group = project.get('project_group', None)
        if self.__modelRid is not None:
            self.model = Model.fetch(self.__modelRid)
        self.dataManageModel = IESPlanDataManageModel(self.id)
        self.planModel = IESLabPlanModel(self.id)
        self.evaluationModel = IESLabPlanEvaluationModel(self.id)
        self.currentPlanResult = IESLabPlanResult(self.id)
        self.currentEvaluationResult = IESLabPlanEvaluationResult(self.id)

    @staticmethod
    def fetch(simulationId):
        """
            获取算例信息
        """
        url = f'api/ieslab-plan/rest/simu/{simulationId}/'
        try:
            r = request('GET', url)
            text = getattr(r, 'text', '')

            try:
                project = json.loads(text) if text else {}
            except Exception:
                project = {}

            # 空响应或非 JSON
            if not project:
                raise Exception(f"获取算例失败（simu_id={simulationId}）：服务返回空响应或非 JSON，url={url}")

            return IESLabPlan(project)

        except Exception as e:
            # 统一上下文信息
            raise Exception(f"获取算例失败（simu_id={simulationId}，url={url}），{e}")


    def __run(self, job=None, name=None):
        '''
            调用仿真 

            :params job:  调用仿真时使用的计算方案，不指定将使用算例保存时选中的计算方案
            :params name:  任务名称，为空时使用项目的参数方案名称和计算方案名称

            :return: 返回一个运行实例
        '''
        if job is None:
            currentJob = self.model.context['currentJob']
            job = self.model.jobs[currentJob]
        job['args']['simulationId'] = self.id
        return self.model.run(job, name=name)

    def iesLabTypicalDayRun(self, job=None, name=None, **kwargs)->Runner[IESLabTypicalDayResult]:
        '''
            运行典型日计算 

            :params job:  调用仿真时使用的计算方案，不指定将使用算例保存时选中的计算方案
            :params name:  任务名称，为空时使用项目的参数方案名称和计算方案名称

            :return: Runner[IESLabTypicalDayResult]
        '''
        if job is None:
            currentJob = self.model.context['currentJob']
            job = self.model.jobs[currentJob]
            if job['rid'] != 'function/CloudPSS/ieslab-gmm':
                for j in self.model.jobs:
                    if j['rid'] == 'job-definition/ies/ies-gmm' or j['rid'] == 'job-definition/cloudpss/ieslab-gmm':
                        j['rid'] = 'function/CloudPSS/ieslab-gmm'
                        job = j
        if job is None:
            raise Exception("找不到默认的综合能源系统规划典型日生成算法的计算方案")
        if job['rid'] != 'function/CloudPSS/ieslab-gmm':
            raise Exception("不是综合能源系统规划典型日生成算法的计算方案")
        return self.__run(job=job, name=name)

    def iesLabEvaluationRun(self, planId, type=None):
        '''
            运行方案评估

            :param planID int类型，表示优化方案的ID，数值位于0~优化方案数量之间
            :param type string类型，表示评估类型，可选值为：能效评价、环保评价

            :return: 方案评估运行实例

        '''
        return self.evaluationModel.run(planId, type)

    def iesLabEnergyEvaluationRun(self, planId):
        '''
            运行能效评价

            :param planID int类型，表示优化方案的ID，数值位于0~优化方案数量之间

            :return: 能效评价运行实例

        '''
        return self.evaluationModel.EnergyEvaluationRun(planId)

    def iesLabEnvironmentalEvaluationRun(self, planId):
        '''
            运行环保评价

            :param planID int类型，表示优化方案的ID，数值位于0~优化方案数量之间

            :return: 环保评价运行实例
        '''
        return self.evaluationModel.EnvironmentalEvaluationRun(planId)

    def iesLabPlanRun(self):
        '''
            生成方案优选算例

            :return: 方案优选运行实例
        '''
        return self.planModel.run()
    
    def iesLabPlanKill(self):
        '''
            停止并删除方案优选算例

            :return: Boolean
        '''
        return self.planModel.kill()

    @staticmethod
    def createProjectGroup(group_name, desc=None, createById=None):
        '''
            创建项目组

            :params group_name: String 项目组名称 
            :params desc: String 项目组描述 可选参数
            :params createById Int 父项目组id  可选参数，如果是从已有项目组导入的项目组，必填此项

            :return: Int 返回创建的项目组id
        '''
        try:
            if createById is None: 
                isImport = 0
            else:
                isImport = 1
            payload = {
                'group_name': group_name,
                'desc': desc,
                'isImport': isImport,
                'createById': createById,
            }
            r = request(
                'POST', 'api/ieslab-plan/rest/projectgroup/', data=json.dumps(payload))
            project = json.loads(r.text)
            return project.get('id', None)
        except Exception as e:
            raise Exception('创建项目组失败')

    @staticmethod  
    def createProject(name, project_group, start_date, end_date, construction_cycle, desc=None, createById=None):
        '''
            创建项目

            :params name: String 项目名称 
            :params project_group: Int 父项目组id
            :param start_date: Int 项目开始年限，范围在[1500,3000]之间
            :param end_date: Int 项目结束年限，范围在项目开始时间之后且不超过五十年
            :param construction_cycle: Int 项目建设周期(年), 必须小于等于 项目结束年限 - 项目开始年限
            :params desc: String 项目描述, 可选参数
            :params createById Int 父项目id, 可选参数, 如果是从已有项目导入的项目，必填此项

            :return: Int 返回创建的项目id
        '''
        try:
            if start_date < 1500 or start_date > 3000:
                raise Exception('项目开始年限错误，范围在[1500,3000]之间')
            if end_date < start_date or end_date > start_date + 50:
                raise Exception('项目结束年限错误，范围在项目开始时间之后且不超过五十年')
            if construction_cycle > end_date - start_date:
                raise Exception('项目建设周期错误，必须小于等于 项目结束年限 - 项目开始年限')
            if createById is None: 
                payload = {
                    'name': name,
                    'project_group': project_group,
                    'start_date': start_date,
                    'end_date': end_date,
                    'construction_cycle': construction_cycle,
                    'desc': desc
                }
            else:
                payload = {
                    'name': name,
                    'project_group': project_group,
                    'start_date': start_date,
                    'end_date': end_date,
                    'construction_cycle': construction_cycle,
                    'desc': desc,
                    'createById': createById
                }
            r = request(
                'POST', 'api/ieslab-plan/rest/simu/', data=json.dumps(payload))
            project = json.loads(r.text)
            return project.get('id', None)
        except Exception as e:
            raise Exception('创建项目失败')

