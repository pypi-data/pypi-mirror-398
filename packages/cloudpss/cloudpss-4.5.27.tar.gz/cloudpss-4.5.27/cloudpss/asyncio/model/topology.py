from cloudpss.asyncio.utils.httpAsyncRequest import graphql_request
from cloudpss.model.topology import ModelTopology as ModelTopologyBase


class ModelTopology(ModelTopologyBase):
    @staticmethod
    async def fetch(hash, implementType, config, maximumDepth=None):
        """
            获取拓扑

            :params: hash 
            :params: implementType 实现类型
            :params: config 参数方案
            :params: maximumDepth 最大递归深度，用于自定义项目中使用 diagram 实现元件展开情况

            : return: 拓扑实例

            >>> data = ModelTopology.fetch('','emtp',{})

        """
        args = {} if config is None else config['args']
        variables = {
            "a": {
                'hash': hash,
                'args': args,
                'acceptImplementType': implementType,
                'maximumDepth': maximumDepth
            }
        }
        data = await graphql_request(ModelTopology.__modelTopologyQuery, variables)
        if 'errors' in data:
            raise Exception(data['errors'][0]['message'])

        return ModelTopology(data['data']['modelTopology'])