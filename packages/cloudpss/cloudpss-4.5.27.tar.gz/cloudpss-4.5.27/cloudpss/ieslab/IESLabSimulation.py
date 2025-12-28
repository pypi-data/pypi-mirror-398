import json
from ..utils import request
from ..model.model import Model
from .DataManageModel import IESSimulationDataManageModel


class IESLabSimulation(object):
    def __init__(self, project={},model:Model=None):
        '''
            初始化
        '''
        self.id = project.get('id', None)
        self.name = project.get('name', None)
        self.__modelRid = project.get('model', None)
        self.project_group = project.get('project_group', None)
        self.model=model
        self.dataManageModel = IESSimulationDataManageModel(self.id)

    @staticmethod
    def fetch(simulationId):
        """
            获取算例信息
        """
        url = f'api/ieslab-simulation/rest/simu/{simulationId}/'
        try:
            r = request('GET', url)
            text = getattr(r, 'text', '')

            try:
                project = json.loads(text) if text else {}
            except Exception:
                project = {}

            # 空响应/非 JSON
            if not project:
                raise Exception(f"获取算例失败（simu_id={simulationId}）：服务返回空响应或非 JSON，url={url}")

            modelRid = project.get('model', None)
            model = None
            if modelRid is not None:
                try:
                    model = Model.fetch(modelRid)
                except Exception as e:
                    model = None

            return IESLabSimulation(project, model)

        except Exception as e:
            # 统一上下文信息
            raise Exception(f"获取算例失败（simu_id={simulationId}，url={url}），{e}")
   
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

        job['args']['simulationId'] = self.id
        return self.model.run(job, name=name)
    
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
                'POST', 'api/ieslab-simulation/rest/projectgroup/', data=json.dumps(payload))
            project = json.loads(r.text)
            return project.get('id', None)
        except Exception as e:
            raise Exception('创建项目组失败')

    @staticmethod 
    def createProject(name, project_group, desc=None, createById=None):
        '''
            创建项目

            :params name: String 项目名称 
            :params project_group: Int 父项目组id,
            :params desc: String 项目描述, 可选参数
            :params createById Int 父项目id, 可选参数, 如果是从已有项目导入的项目，必填此项

            :return: Int 返回创建的项目id
        '''
        try:
            if createById is None: 
                payload = {
                    'name': name,
                    'project_group': project_group,
                    'desc': desc
                }
            else:
                payload = {
                    'name': name,
                    'project_group': project_group,
                    'desc': desc,
                    'createById': createById
                }
            r = request(
                'POST', 'api/ieslab-simulation/rest/simu/', data=json.dumps(payload))
            project = json.loads(r.text)
            return project.get('id', None)
        except Exception as e:
            raise Exception('创建项目失败')
