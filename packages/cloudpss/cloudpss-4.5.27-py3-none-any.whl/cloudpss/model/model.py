import os
import re
from copy import deepcopy
from cloudpss.job.job import Job
from cloudpss.job.result import EMTResult, IESResult, PowerFlowResult
from cloudpss.job.result.result import Result
from cloudpss.utils.IO import IO
from cloudpss.utils import graphql_request
from .revision import ModelRevision
from .jobDefinitions import JOB_DEFINITIONS
from ..verify import userName

from cloudpss.runner.result import IESResult
from cloudpss.runner.runner import Runner


class Model(object):
    """
    CloudPSS工程类，用于处理加载后的工程数据

    实例变量说明：

    rid         项目的 rid

    name         项目的名称

    description  项目的描述

    revision    当前项目的版本信息

    configs     当前项目的所有参数方案

    jobs        当前项目的所有计算方案

    context     当前项目的上下文相关信息

    """
    __models_query="""query($input:ModelsInput!){models(input:$input){cursor total count items{rid name description owner tags updatedAt }}}"""
    
    __model_query= """
            query  t($rid:ResourceId!){
                model(input:{rid: $rid}) {
                    configs
                    context
                    description
                    jobs
                    name
                    rid
                    tags
                    permissions {
                        moderator
                        member
                        everyone
                    }
                    revision {
                        author
                        documentation
                        graphic
                        hash
                        implements
                        message
                        parameters
                        pins
                        version
                    }
                }
            }
        """
    __create_model= """mutation($a:CreateModelInput!){createModel(input:$a){rid}}"""
    __update_model = """mutation($a:UpdateModelInput!){updateModel(input:$a){rid}}"""

    context: dict
    jobs: list
    configs: list

    def __init__(self, model: dict = {}):
        """
        项目初始化
        """
        for k, v in model.items():
            if k == "revision":
                if "version" in v and v["version"] < 5:
                    self.revision = ModelRevision(v)
                else:
                    raise Exception(
                        "当前SDK版本（ver 3.X.X）不兼容该项目文件，请先升级项目文件。具体方法：将该项目文件导入至XStudio 3.X.X平台后重新保存至本地后即可。"
                    )

            else:
                self.__dict__[k] = v

    def __getitem__(self, attr):
        return super(Model, self).__getattribute__(attr)

    def toJSON(self):
        """
        类对象序列化为 dict
        :return: dict
        """
        model = {**self.__dict__, "revision": self.revision.toJSON()}
        return model

    def getAllComponents(self)->dict:
        """
        获取实现

        :return: 所有元件信息

        >>> model.getAllComponents()
        {
            'canvas_0_2': Component 实例
        }
        """
        diagramImplement = self.revision.getImplements().getDiagram()
        if diagramImplement is None:
            raise ValueError("不存在拓扑实现")
        return diagramImplement.getAllComponents()
    
    def addComponent(self, definition, label, args, pins, canvas=None, position=None, size=None):
        """
        创建一个

        :return: Component

        >>>> model.addComponent(args)
        """
        diagramImplement = self.revision.getImplements().getDiagram()
        if diagramImplement is None:
            raise ValueError("不存在拓扑实现")
        return diagramImplement.addComponent(definition, label, args, pins, canvas, position, size)
    
    def removeComponent(self, key):
        """
        删除元件实现

        :return: boolean

        >>>> model.removeComponent(key)
        """
        diagramImplement = self.revision.getImplements().getDiagram()
        if diagramImplement is None:
            raise ValueError("不存在拓扑实现")
        return diagramImplement.removeComponent(key)
    
    def updateComponent(self, key, **kwargs):
        """
        更新元件实现

        :return: bool

        >>>> model.updateComponent(key, args)
        """
        diagramImplement = self.revision.getImplements().getDiagram()
        if diagramImplement is None:
            raise ValueError("不存在拓扑实现")
        return diagramImplement.updateComponent(key, **kwargs)


    def getComponentsByRid(self, rid: str):
        """
        通过指定元件类型获取元件

        :params str: 元件类型

        :type rid: str

        :return: 按照元件的 rid 过滤后的 dict<>

        >>> model.getComponentsByRid('model/CloudPSS/newInductorRouter')
        {
            'canvas_0_2': Component 实例
        }

        """

        v = self.getAllComponents()

        cells = {}
        for key, val in v.items():
            if not val.shape.startswith("diagram-component"):
                continue
            if val.definition == rid:
                cells[key] = val
        return cells

    def getComponentByKey(self, componentKey: str):
        """
        通过元件的 key 获取对应的元件

        :params key: key 元件的key

        :Return: Component 实例

        >>> model.getComponentByKey('canvas_0_757')
        Component 实例
        """

        v = self.getAllComponents()
        return v[componentKey]

    def getModelJob(self, name):
        """
        获取指定名称的计算方案

        :params Name: Name 参数名称

        :return: 同名计算方案数组

        >>> model.getModelJob('电磁暂态方案 1')
        """
        jobs = []

        for val in self.jobs:
            if val["name"] == name:
                jobs.append(val)

        return jobs

    def createJob(self, jobType:str, name:str):
        """
        创建一个计算方案
        创建出的方案默认不加入到项目中，需要加入请调用 addJob

        :params jobType:  方案类型
            电磁暂态仿真方案 emtp
            移频电磁暂态仿真方案 sfemt
            潮流计算方案 powerFlow

        :return: 返回一个指定类型的计算方案

        >>> model.createJob('emtp','emtp job')
        计算方案
        """
        job = deepcopy(JOB_DEFINITIONS[jobType])
        job["name"] = name
        return job

    def addJob(self, job: dict):
        """
        将计算方案添加到工程中

        :params job:  计算方案 dict

        >>> job = model.createJob('emtp','emtp job')
            model.addJob(job)
        """

        self.jobs.append(job)

    def getModelConfig(self, name):
        """
        获取指定名称的参数方案

        :params name:  参数方案名称

        :return: 同名的方案数组

        >>> model.getModelConfig('参数方案 1')
        """
        configs = []

        for val in self.configs:
            if val["name"] == name:
                configs.append(val)

        return configs

    def createConfig(self, name):
        """
        创建一个参数方案
        根据项目的第一个参数方案生成一个方案
        创建出的方案默认不加入到项目中，需要加入请调用 addConfig
        :params name:  参数方案名称

        :return: 返回一个参数方案 dict

        >>> job = model.createConfig('my config')
            参数方案
        """

        config = deepcopy(self.configs[0])
        config['name'] = name
        self.__updateConfigDefault(config)
        return config

    def addConfig(self, config):
        """
        将参数方案添加到工程中

        :params config:  参数方案 dict

        >>> config = model.createConfig('my config')
            model.addConfig(config)
        """

        self.configs.append(config)
        self.__updateConfigDefault(config)
        return config

    @staticmethod
    def fetchMany(name=None, cursor=[], pageSize=10,owner=None,**kwargs):
        """
        获取用户可以运行的项目列表

        :params name:  查询名称，模糊查询
        :params cursor:  游标

        :return: 按分页信息返回项目列表

        >>> data= await Model.fetchMany()
        [
            {'rid': 'model/demo/demo', 'name': 'demo', 'description': 'demo'}
            ...
        ]

        """
        if owner is None:
            owner = userName()
        elif owner == "*":
            owner = None
        variables = {
            "cursor": cursor,
            "limit": pageSize,
            "orderBy": [
                "updatedAt<",
                "type",
                "owner",
                "key"
            ],
            "owner":owner,
        }
        if name is not None:
            variables["_search"] = name

        data = graphql_request(Model.__models_query, {"input": variables},**kwargs)
        if "errors" in data:
            raise Exception(data["errors"][0]["message"])
        return data["data"]["models"]['items']

    @staticmethod
    def fetch(rid,**kwargs):
        """
        获取项目

        :params rid:  项目 rid

        :return: 返回一个项目实例

        >>> model=Model.fetch('model/Demo/test')

        """
        data = graphql_request(Model.__model_query, {"rid": rid},**kwargs)
        if "errors" in data:
            raise Exception(data["errors"][0]["message"])
        return Model(data["data"]["model"])

    def run(self, job=None, config=None, name=None, **kwargs):
        """

            调用仿真 

            :params job:  调用仿真时使用的计算方案，不指定将使用算例保存时选中的计算方案
            :params config:  调用仿真时使用的参数方案，不指定将使用算例保存时选中的参数方案
            :params name:  任务名称，为空时使用项目的参数方案名称和计算方案名称

            :return: 返回一个运行实例

            >>> runner=model.run(job,config,'')
            runner

        """
        if job is None:
            currentJob = self.context['currentJob']
            job = self.jobs[currentJob]
        if config is None:
            currentConfig = self.context['currentConfig']
            config = self.configs[currentConfig]
        self.__updateConfigDefault(config)
        return self.revision.run(job, config, name, rid=self.rid, **kwargs)

 
    def iesSimulationRun(self, job=None, config=None, name=None, **kwargs):
        return self.run(job=job, config=config, name=name, kwargs=kwargs)

    @staticmethod
    def load(filePath, format="yaml"):
        """
        加载本地项目文件

        :params file:  文件目录

        :format 默认格式为yaml

        :return: 返回一个项目实例

        >>> model = Model.load('filePath')

        """

        if not os.path.exists(filePath):
            raise FileNotFoundError("未找到文件")
        data = IO.load(filePath, format)
        return Model(data)


    @staticmethod
    def dump(model, file, format="yaml", compress="gzip"):
        """
        下载项目文件

        :params model:  项目
        :params file:  文件路径
        :params format:  文件格式
        :params compress:  是否压缩 压缩格式目前支持gzip 为None时不压缩

        :return: 无

        >>> Model.dump(model,file)
        """

        IO.dump(model.toJSON(), file, format, compress)

    def save(self, key=None):
        """
        保存/创建项目

        key 不为空时如果远程存在相同的资源名称时将覆盖远程项目。
        key 为空时如果项目 rid 不存在则抛异常，需要重新设置 key。
        如果保存时，当前用户不是该项目的拥有者时，将重新创建项目，重建项目时如果参数的 key 为空将使用当前当前项目的 key 作为资源的 key ，当资源的 key 和远程冲突时保存失败

        :params: key 资源 id 的唯一标识符，

        :return: 保存成功/保存失败

        >>> model.save(model)
            model.save(model,'newKey') # 另存为新的项目

        """
        username = userName()

        if key is not None:
            matchObj = re.match(r"^[-_A-Za-z0-9]+$", key, re.I | re.S)
            if matchObj:
                self.rid = "model/" + username + "/" + key
                try:
                    return Model.update(self)
                except:
                    return Model.create(self)
            else:
                raise Exception("key 能包含字母数子和下划线")
        else:
            t = "(?<=/)\\S+(?=/)"
            owner = re.search(t, self.rid)
            if owner is None:
                raise Exception("rid 错误，请传入 key")
            elif owner[0] != username:
                rid = re.sub(t, username, self.rid)
                try:
                    return Model.create(self)
                except:
                    raise Exception(rid + " 该资源已存在，无法重复创建,请修改 key")

        return Model.update(self)


    @staticmethod
    def create(model,**kwargs):
        """
        新建项目

        :params: model 项目

        :return: 保存成功/保存失败

        >>> Model.create(model)
        保存成功
        """
        # Model.update(model)
        t = "(?<=/)\\S+(?=/)"
        username = userName()
        owner = re.search(t, model.rid)

        if owner is None:
            raise Exception("rid 错误，无法保存")
        elif owner[0] != username:
            raise Exception("rid 错误，无法保存")

        revision = ModelRevision.create(model.revision, model.revision.hash)

        # 使用默认权限对象，但如果model的permissions字段中有相关权限值就使用model中的数值
        default_permissions = {
            "moderator": 98367,
            "member": 65551,
            "everyone": 0
        }
        
        # 如果model有permissions字段，则合并权限值
        model_permissions = getattr(model, 'permissions', {})
        if isinstance(model_permissions, dict):
            permissions = {**default_permissions, **model_permissions}
        else:
            permissions = default_permissions

        return graphql_request(
            Model.__create_model,
            {
                "a": {
                    "rid": model.rid,
                    "revision": revision["hash"],
                    "context": model.context,
                    "configs": model.configs,
                    "jobs": model.jobs,
                    "name": model.name,
                    "description": model.description,
                    "tags": model.tags,
                    "permissions": permissions,
                }
            },
            **kwargs
        )

    

    @staticmethod
    def update(model,**kwargs):
        """
        更新项目

        :params: model 项目

        :return: 保存成功/保存失败

        >>> Model.update(model)
        """

        t = "(?<=/)\\S+(?=/)"
        username = userName()
        owner = re.search(t, model.rid)

        if owner is None:
            raise Exception("rid 错误，无法保存")
        elif owner[0] != username:
            raise Exception("rid 错误，无法保存")

        
        permissions=model.permissions
        revision = ModelRevision.create(model.revision, model.revision.hash)

        xVersion = int(float(os.environ.get('X_CLOUDPSS_VERSION', 4)))
        tags= {
            "replace":model.tags
        }
        if xVersion==3:
            tags=model.tags
        
        # 使用默认权限对象，但如果model的permissions字段中有相关权限值就使用model中的数值
        default_permissions = {
            "moderator": 98367,
            "member": 65551,
            "everyone": 0
        }
        
        # 如果model有permissions字段，则合并权限值
        model_permissions = getattr(model, 'permissions', {})
        if isinstance(model_permissions, dict):
            permissions = {**default_permissions, **model_permissions}
        else:
            permissions = default_permissions

        r= graphql_request(
            Model.__update_model, {
                'a': {
                    'rid': model.rid,
                    'revision': revision['hash'],
                    'context': model.context,
                    'configs': model.configs,
                    'jobs': model.jobs,
                    'name': model.name,
                    'description': model.description,
                    'tags': tags,
                    "permissions": permissions,
                }
            },**kwargs)
        if "errors" in r:
            raise Exception(r["errors"][0]["message"])
        return r


    
    def fetchTopology(
        self,
        implementType=None,
        config=None,
        maximumDepth=None,
         **kwargs
    ):
        """
        通过项目信息，获取当前项目对应的拓扑数据

        :params implementType:  实现类型
        :params config: config 项目参数, 不指定将使用算例保存时选中的参数方案
        :params maximumDepth:  最大递归深度，用于自定义项目中使用 diagram 实现元件展开情况

        :return:  一个拓扑实例

        >>> topology=model.fetchTopology()
            topology=model.fetchTopology(implementType='powerFlow',config=config) # 获取潮流实现的拓扑数据
            topology=model.fetchTopology(maximumDepth=2) # 获取仅展开 2 层的拓扑数据
        """
        if self.revision is not None:
            if implementType is None:
                implementType = "emtp"
            if config is None:
                currentConfig = self.context["currentConfig"]
                config = self.configs[currentConfig]
            return self.revision.fetchTopology(implementType, config,
                maximumDepth, **kwargs)
        return None
    

    def __updateConfigDefault(self, config):
        paramters = self.revision.parameters
        if paramters is None:
            return
        for param in paramters:
            for val in param['items']:
                if config['args'].get(val['key'],None) is None:
                    config['args'][val['key']] = val['value']
    
    def runEMT(self,job=None,config=None,**kwargs)->Runner[EMTResult]:
        """
            运行 emtp 内核，如果当前 model 没有创建  Job 时报错，默认使用第一个计算方案，进行仿真。

            :params job:  调用仿真时使用的计算方案，不指定将使用算例保存时选中的计算方案
            :params config:  调用仿真时使用的参数方案，不指定将使用算例保存时选中的参数方案
            :params name:  任务名称，为空时使用项目的参数方案名称和计算方案名称

            :return: 返回一个运行实例

            >>> runner=model.run(job,config,'')
            runner

        """
        if job is None:
            currentJob = self.context["currentJob"]
            job = self.jobs[currentJob]
        if config is None:
            currentConfig = self.context["currentConfig"]
            config = self.configs[currentConfig]
        return self.revision.run(
            job, config, name,  policy, stop_on_entry,self.rid,**kwargs
        )
        
    def __findJob(self, jobType):
        currentJob = self.context["currentJob"]
        job = self.jobs[currentJob]
        if job["rid"] != jobType:
            for j in self.jobs:
                if j["rid"] ==jobType:
                    job = j
        return job        
        
    def runEMT(self, job=None, config=None,**kwargs) -> Job[EMTResult]:
        """
        运行 emtp 内核，如果当前 model 没有创建  Job 时报错，默认使用算例中选中的计算方案进行仿真，如果选中的计算方案不是 EMT 方案则选第一个EMT 计算方案，如果不存在计算方案则直接报错。

        :param: job 计算方案名称，可选，字符串类型或者字典类型,默认使用第一个计算方案，如果同名使用最靠前一个
        :param: config 参数方案，可选，字符串类型或者字典类型,默认使用保存时选中的参数方案

        :return: 生成的任务
        """
        if job is None:
            job = self.__findJob("function/CloudPSS/emtps")
        if job is None:
            raise Exception("找不到电磁暂态运行的计算方案")
        if job["rid"] != "function/CloudPSS/emtp" and job["rid"] != "function/CloudPSS/emtps":
            raise Exception("不是电磁暂态运行生成算法的计算方案")
        if config is None:
            currentConfig = self.context["currentConfig"]
            config = self.configs[currentConfig]
        
        return self.run(job=job, config=config,**kwargs)

    def runSFEMT(self,job=None,config=None,**kwargs)->Runner[EMTResult]:
        """
            运行 移频电磁暂态 内核，如果当前 model 没有创建  Job 时报错，默认使用第一个计算方案，进行仿真。

        :param: job 计算方案名称，可选，字符串类型或者字典类型,默认使用第一个计算方案，如果同名使用最靠前一个
        :param: config 参数方案，可选，字符串类型或者字典类型,默认使用保存时选中的参数方案

        :return: Job[EMTView]
        """
        if job is None:
            job = self.__findJob("function/CloudPSS/sfemt")
        if job is None:
            raise Exception("找不到移频电磁暂态运行的计算方案")
        if job["rid"] != "function/CloudPSS/sfemt":
            raise Exception("不是移频电磁暂态运行生成算法的计算方案")
        if config is None:
            currentConfig = self.context["currentConfig"]
            config = self.configs[currentConfig]
        return self.run(job=job, config=config,**kwargs)

    def runPowerFlow(self,job=None,config=None,**kwargs)->Runner[PowerFlowResult]:
        """
            运行 潮流 内核，如果当前 model 没有创建  Job 时报错，默认使用第一个计算方案，进行仿真。

            :param: job 计算方案名称，可选，字符串类型或者字典类型,默认使用第一个计算方案，如果同名使用最靠前一个
            :param: config 参数方案，可选，字符串类型或者字典类型,默认使用保存时选中的参数方案

            :return: Job[EMTView]
        """
        if job is None:
            job = self.__findJob("function/CloudPSS/power-flow")
        if job is None:
            raise Exception("找不到潮流内核运行的计算方案")
        if job["rid"] != "function/CloudPSS/power-flow":
            raise Exception("不是潮流内核运行生成算法的计算方案")
        if config is None:
            currentConfig = self.context["currentConfig"]
            config = self.configs[currentConfig]
        return self.run(job=job, config=config,**kwargs)

    def runThreePhasePowerFlow(self, job=None, config=None,**kwargs) -> Job[PowerFlowResult]:
        """
        运行 三相不平衡潮流 内核，如果当前 model 没有创建  Job 时报错，默认使用第一个计算方案，进行仿真。

        :param: job 计算方案名称，可选，字符串类型或者字典类型,默认使用第一个计算方案，如果同名使用最靠前一个
        :param: config 参数方案，可选，字符串类型或者字典类型,默认使用保存时选中的参数方案

        :return: Job[PowerFlowView]
        """
        if job is None:
            job = self.__findJob("function/CloudPSS/three-phase-powerFlow")
        if job is None:
            raise Exception("找不到三相不平衡潮流内核运行的计算方案")
        if job["rid"] != "function/CloudPSS/three-phase-powerFlow":
            raise Exception("不是三相不平衡潮流内核运行生成算法的计算方案")
        if config is None:
            currentConfig = self.context["currentConfig"]
            config = self.configs[currentConfig]
        return self.run(job=job, config=config,**kwargs)

    def runIESLoadPrediction(self, job=None, config=None,**kwargs) -> Job[IESResult]:
        """
        运行 负荷预测方案 内核，如果当前 model 没有创建  Job 时报错，默认使用第一个计算方案，进行仿真。

        :param: job 计算方案名称，可选，字符串类型或者字典类型,默认使用第一个计算方案，如果同名使用最靠前一个
        :param: config 参数方案，可选，字符串类型或者字典类型,默认使用保存时选中的参数方案

        :return: Job[IESView]
        """
        if job is None:
            job = self.__findJob("job-definition/ies/ies-load-prediction")
        if job is None:
            raise Exception("找不到负荷预测方案内核运行的计算方案")
        if job["rid"] != "job-definition/ies/ies-load-prediction":
            raise Exception("不是负荷预测方案内核运行生成算法的计算方案")
        if config is None:
            currentConfig = self.context["currentConfig"]
            config = self.configs[currentConfig]
        return self.run(job=job, config=config)

    def runIESPowerFlow(self, job=None, config=None,**kwargs) -> Job[IESResult]:
        """
        运行 时序潮流方案 内核，如果当前 model 没有创建  Job 时报错，默认使用第一个计算方案，进行仿真。

        :param: job 计算方案名称，可选，字符串类型或者字典类型,默认使用第一个计算方案，如果同名使用最靠前一个
        :param: config 参数方案，可选，字符串类型或者字典类型,默认使用保存时选中的参数方案

        :return: Job[IESView]
        """
        if job is None:
            job = self.__findJob("job-definition/ies/ies-power-flow")
        if job is None:
            raise Exception("找不到时序潮流方案内核运行的计算方案")
        if job["rid"] != "job-definition/ies/ies-power-flow":
            raise Exception("不是时序潮流方案内核运行生成算法的计算方案")
        if config is None:
            currentConfig = self.context["currentConfig"]
            config = self.configs[currentConfig]
        return self.run(job=job, config=config,**kwargs)

    def runIESEnergyStoragePlan(self, job=None, config=None,**kwargs) -> Job[IESResult]:
        """
        运行 储能规划方案 内核，如果当前 model 没有创建  Job 时报错，默认使用第一个计算方案，进行仿真。

        :param: job 计算方案名称，可选，字符串类型或者字典类型,默认使用第一个计算方案，如果同名使用最靠前一个
        :param: config 参数方案，可选，字符串类型或者字典类型,默认使用保存时选中的参数方案

        :return: Job[IESView]
        """
        if job is None:
            job = self.__findJob("job-definition/ies/ies-energy-storage-plan")
        if job is None:
            raise Exception("找不到储能规划方案内核运行的计算方案")
        if job["rid"] != "job-definition/ies/ies-energy-storage-plan":
            raise Exception("不是储能规划方案内核运行生成算法的计算方案")
        if config is None:
            currentConfig = self.context["currentConfig"]
            config = self.configs[currentConfig]
        return self.run(job=job, config=config,**kwargs)

