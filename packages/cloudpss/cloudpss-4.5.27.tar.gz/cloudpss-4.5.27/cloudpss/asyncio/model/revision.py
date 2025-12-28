from cloudpss.asyncio.utils.httpAsyncRequest import graphql_request
from cloudpss.model.revision import ModelRevision as ModelRevisionBase


class ModelRevision(ModelRevisionBase):
    
    @staticmethod
    async def create(revision, parentHash=None):
        """
            创建一个新版本

            :params: revision 版本数据

            :return: 项目版本hash

            >>> ModelRevision.create(model.revision)
            {hash:'4043acbddb9ce0c6174be65573c0380415bc48186c74a459f88865313743230c'}
        """

        r = revision.toJSON()
        del r['hash']
        variables = {'a': {**r, 'parent': parentHash}}
        r = await graphql_request(ModelRevision.__createModelRevisionQuery, variables)
        if 'errors' in r:
            raise Exception(r['errors'])
        return r['data']['createModelRevision']
    
    async def run(self, job, config, name=None, rid='', policy=None, **kwargs):
        """
            运行某个指定版本的项目

            :params job:  调用仿真时使用的计算方案，为空时使用项目的第一个计算方案
            :params config:  调用仿真时使用的参数方案，为空时使用项目的第一个参数方案
            :params name:  任务名称，为空时使用项目的参数方案名称和计算方案名称
            :params rid:  项目rid，可为空

            :return: 返回一个ModelRevision

            >>> revision.run(revision,job,config,'')
        """
        return await ModelRevision.create(self)