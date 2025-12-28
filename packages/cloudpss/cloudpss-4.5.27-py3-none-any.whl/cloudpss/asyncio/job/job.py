from cloudpss.asyncio.job.messageStreamReceiver import MessageStreamReceiver
from cloudpss.asyncio.job.messageStreamSender import MessageStreamSender
from cloudpss.asyncio.utils.AsyncIterable import CustomAsyncIterable
from cloudpss.asyncio.utils.httpAsyncRequest import graphql_request
from cloudpss.job import Job as JobBase
from typing import Any, Callable, TypeVar
F = TypeVar('F', bound=Callable[..., Any])

class Job(JobBase):
    
    @staticmethod
    async def fetch(id):
        """
        获取job信息
        """
        if id is None:
            raise Exception("id is None")
       
        variables = {"_a": {"id": id}}

        r = await graphql_request(Job.__jobQuery, variables)
        if "errors" in r:
            raise Exception(r["errors"])
        return Job(**r["data"]["job"])
    
    @staticmethod
    def fetchMany(*args):
        """
        批量获取任务信息
        """
        jobs = CustomAsyncIterable(Job.fetch,*args)
        return jobs
    
    
    @staticmethod
    async def create(revisionHash, job, config, name=None, rid="", policy=None, **kwargs):
        """
        创建一个运行任务

        :params: revision 项目版本号
        :params: job 调用仿真时使用的计算方案，为空时使用项目的第一个计算方案
        :params: config 调用仿真时使用的参数方案，为空时使用项目的第一个参数方案
        :params: name 任务名称，为空时使用项目的参数方案名称和计算方案名称
        :params: rid 项目rid，可为空

        :return: 返回一个运行实例

        >>> runner = Runner.runRevision(revision,job,config,'')
        """
        
        variables=Job.__createJobVariables(job, config, revisionHash, rid, policy)
        r = await graphql_request(Job.__createJobQuery, variables)
        if "errors" in r:
            raise Exception(r["errors"])
        id = r["data"]["job"]["id"]
        return await Job.fetch(id)
    
    
    @staticmethod
    async def abort(id, timeout):
        """
        结束当前运行的算例

        """
        query = """mutation ($input: AbortJobInput!) {
            job: abortJob(input: $input) {
                id
                status
            }
        }
        """
        variables = {"input": {"id": id, "timeout": timeout}}
        await graphql_request(query, variables)
        
    async def result(self, resultType:F)->F:
        """
        获取当前运行实例的输出
        """
        receiver = await self.read()
        sender = await self.write()
        self._result= resultType(receiver, sender)
        return self._result
    
    async def write(self, sender=None, dev=False, **kwargs) -> MessageStreamSender:
        """
        使用发送器为当前运行实例输入
        """

        if sender is not None:
            self.__sender = sender
        if self.__sender is None:
            self.__sender = MessageStreamSender(self, dev)
        await self.__sender.connect(**kwargs)
        return self.__sender
    
    async def read(self, receiver=None, dev=False, **kwargs)-> MessageStreamReceiver:
        """
        使用接收器获取当前运行实例的输出
        """
        if receiver is not None:
            self.__receiver = receiver
        if self.__receiver is None:
            self.__receiver = MessageStreamReceiver(self, dev)
        await self.__receiver.connect(**kwargs)
        return self.__receiver
    
    async def status(self):
        """
        return: 0: 运行中 1: 运行完成 2: 运行失败
        """
        if self.__receiver is not None:
            return await self.__receiver.status
        # if self.__receiver is None:
        #     self.__connect()
        # return 0
        return 0