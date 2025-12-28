from cloudpss.job.job import Job
from .topology import ModelTopology
from .implements import ModelImplement
from ..utils import  graphql_request


class ModelRevision(object):
    
    """
        表示一个项目的版本数据

        实例变量说明：

        implements          项目当前版本的实现数据

        parameters          项目当前版本的参数结果

        pins                项目当前版本的引脚信息

        documentation       项目当前版本的文档信息



    """
    
    __createModelRevisionQuery = """
                    mutation($a:CreateModelRevisionInput!){createModelRevision(input:$a){
                            hash
                    }}
                """

    def __init__(self, revision: dict = {}):
        """
            初始化
        """
        for k, v in revision.items():
            if k == 'implements':
                self.__dict__[k] = ModelImplement(v)
            else:
                self.__dict__[k] = v

    def __getitem__(self, attr):
        return super(ModelRevision, self).__getattribute__(attr)

    def toJSON(self):
        """
            类对象序列化为 dict
            :return: dict
        """

        revision = {**self.__dict__, 'implements': self.implements.toJSON()}
        return revision

    def getImplements(self):
        """
            获取当前版本的实现

            :return: 实现实例

            >>> revision.getImplements()
        """

        return self.implements
    
    def run(self, job, config, name=None, policy=None,stop_on_entry=None,rid=None, **kwargs):
        """
            运行当前版本

            :params job:  调用仿真时使用的计算方案，为空时使用项目的第一个计算方案
            :params config:  调用仿真时使用的参数方案，为空时使用项目的第一个参数方案
            :params name:  任务名称，为空时使用项目的参数方案名称和计算方案名称
            :params rid:  项目rid，可为空

            :return: 返回一个运行实例

            >>> revision.run(revision,job,config,'')
        """
        
        revision= ModelRevision.create(self,**kwargs)
        if stop_on_entry is not None:
            job['args']['stop_on_entry'] = stop_on_entry
        return Job.create(
            revision["hash"], job, config, name=name, rid=rid, policy=policy, **kwargs
        )
    

    @staticmethod
    def create(revision, parentHash=None, **kwargs):
        """
            创建一个新版本

            :params: revision 版本数据

            :return: 项目版本hash

            >>> ModelRevision.create(model.revision)
            {hash:'4043acbddb9ce0c6174be65573c0380415bc48186c74a459f88865313743230c'}
        """
        r = revision.toJSON()
        if 'hash' in r:
            del r['hash']
        variables = {'a': {**r, 'parent': parentHash}}
        r = graphql_request(ModelRevision.__createModelRevisionQuery, variables,**kwargs)
        if 'errors' in r:
            raise Exception(r['errors'])
        
        return r['data']['createModelRevision']
        
    

    def fetchTopology(self, implementType, config, maximumDepth, **kwargs):
        """
            获取当前项目版本的拓扑数据

            :params implementType:  实现类型
            :params config:  项目参数
            :params maximumDepth:  最大递归深度，用于自定义项目中使用 diagram 实现元件展开情况

            :return:  一个拓扑实例

            >>> topology=revision.fetchTopology()
                topology=revision.fetchTopology(implementType='powerFlow',config=config) # 获取潮流实现的拓扑数据
                topology=revision.fetchTopology(maximumDepth=2) # 获取仅展开 2 层的拓扑数据

        """

        if self.hash is not None:
            return ModelTopology.fetch(self.hash, implementType, config,
                                       maximumDepth, **kwargs)
        return None

