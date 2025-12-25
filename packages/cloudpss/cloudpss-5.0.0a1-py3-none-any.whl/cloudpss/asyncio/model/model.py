import os
import re
from cloudpss.asyncio.job.job import Job
from cloudpss.asyncio.model.revision import ModelRevision
from cloudpss.asyncio.utils.httpAsyncRequest import graphql_request
from cloudpss.model.model import Model as ModelBase
from cloudpss.verify import userName


class Model(ModelBase):
    
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
    @staticmethod
    async def fetch(rid):
        """
        获取项目

        :params rid:  项目 rid

        :return: 返回一个项目实例

        >>> model=Model.fetch('model/Demo/test')

        """
        data = await graphql_request(Model.__model_query, {"rid": rid})
        if "errors" in data:
            raise Exception(data["errors"][0]["message"])
        return Model(data["data"]["model"])

    async def save(self, key=None):
        """
        保存/创建项目

        key 不为空时如果远程存在相同的资源名称时将覆盖远程项目。
        key 为空时如果项目 rid 不存在则抛异常，需要重新设置 key。
        如果保存时，当前用户不是该项目的拥有者时，将重新创建项目，重建项目时如果参数的 key 为空将使用当前当前项目的 key 作为资源的 key ，当资源的 key 和远程冲突时保存失败

        :params: model 项目
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
                    return await Model.update(self)
                except:
                    return await Model.create(self)
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
                    return await Model.create(self)
                except:
                    raise Exception(rid + " 该资源已存在，无法重复创建,请修改 key")

        return await Model.update(self)

    @staticmethod
    async def fetchMany(name=None, cursor=[]):
        """
        获取用户可以运行的项目列表

        :params name:  查询名称，模糊查询
        :params cursor:  游标

        :return: 按分页信息返回项目列表

        >>> data= await Model.fetchMany()
        {
            items: [
                {'rid': 'model/admin/share-test', 'name': '1234', 'description': '1234'}
                ...
            ],
            cursor: ["1699353593000"],

        }


        """
        variables = {
            "cursor": cursor,
            "limit": 10,
            "orderBy": ["updatedAt<"],
            "permissionEveryone": ["b_any", 2**16],
        }
        if name is not None:
            variables["_search"] = name

        data = await graphql_request(Model.__models_query, {"input": variables})

        if "errors" in data:
            raise Exception(data["errors"][0]["message"])

        return data["data"]["models"]


    @staticmethod
    async def create(model):
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

        isPublic = model.context.get("auth", "") != "private"
        publicRead = model.context.get("publicRead", "") != False
        auth = (65539 if publicRead else 65537) if isPublic else 0
        revision = await ModelRevision.create(model.revision, model.revision.hash)

        return await graphql_request(
            Model.__models_query,
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
                    "permissions": {
                        "moderator": 1,
                        "member": 1,
                        "everyone": auth,
                    },
                }
            },
        )
        
        
    @staticmethod
    async def update(model):
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

        
        isPublic = model.context.get("auth", "") != "private"
        isComponent = model.context.get("category", "") == "component"
        publicRead = model.context.get("publicRead", "") != False
        auth = (65539 if publicRead else 65537) if isPublic else 0
        revision = await ModelRevision.create(model.revision, model.revision.hash)

        xVersion = int(float(os.environ.get("X_CLOUDPSS_VERSION", 4)))
        tags = {"replace": model.tags}
        if xVersion == 3:
            tags = model.tags

        return await graphql_request(
            Model.__update_model,
            {
                "a": {
                    "rid": model.rid,
                    "revision": revision["hash"],
                    "context": model.context,
                    "configs": model.configs,
                    "jobs": model.jobs,
                    "name": model.name,
                    "description": model.description,
                    "tags": tags,
                    "permissions": {
                        "moderator": 1,
                        "member": 1,
                        "everyone": auth,
                    },
                }
            },
        )

    async def run(self, job=None, config=None, name=None, policy=None,stop_on_entry=None, **kwargs):
        """

        调用仿真

        :params job:  调用仿真时使用的计算方案，不指定将使用算例保存时选中的计算方案
        :params config:  调用仿真时使用的参数方案，不指定将使用算例保存时选中的参数方案
        :params name:  任务名称，为空时使用项目的参数方案名称和计算方案名称

        :return: 返回一个Job实例

        >>> job=model.run(job,config,'')
        job

        """
        if job is None:
            currentJob = self.context["currentJob"]
            job = self.jobs[currentJob]
        if config is None:
            currentConfig = self.context["currentConfig"]
            config = self.configs[currentConfig]
        revision = await self.revision.run(
            job, config, name, self.rid, policy, **kwargs
        )
        if stop_on_entry is not None:
            job['args']['stop_on_entry'] = stop_on_entry
        return await Job.create(
            revision["hash"], job, config, name, self.rid, policy, **kwargs
        )
