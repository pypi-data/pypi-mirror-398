from cProfile import run
import threading
import json
import time
import random

from deprecated import deprecated

from cloudpss.utils.graphqlUtil import graphql_request
from cloudpss.utils.parseDebugArgs import parse_debug_args
from .receiver import Receiver
from .MessageStreamReceiver import MessageStreamReceiver
from .result import IESLabSimulationResult, PowerFlowResult, EMTResult, Result, IESResult
from .IESLabPlanResult import IESLabPlanResult, IESLabOptResult
from .IESLabEvaluationResult import IESLabEvaluationResult, IESLabPlanEvaluationResult, IESLabOptEvaluationResult
# from .IESLabTypicalDayResult import IESLabTypicalDayResult
from ..job.result.IESLabTypicalDayResult import IESLabTypicalDayResult
from .storage import Storage
from ..utils import request
from typing import  TypeVar,  Generic
from .DSLabResult import DSLabResult
import re

RECEIVER = {
    'default': MessageStreamReceiver,
}
T = TypeVar('T', Result, EMTResult, PowerFlowResult, IESResult,
            IESLabSimulationResult, IESLabPlanResult, IESLabEvaluationResult,
            IESLabTypicalDayResult)

IES_LAB_RESULT = {
    'function/ieslab/plan': IESLabPlanResult,
    'function/ieslab/evaluation': IESLabPlanEvaluationResult,
}

IES_LAB_OPT_RESULT = {
    'function/ieslab/plan': IESLabOptResult,
    'function/ieslab/evaluation': IESLabOptEvaluationResult,
}

DS_LAB_RESULT = {
    'function/ieslab/evaluation': DSLabResult
}

RESULT_DB = {
    'function/CloudPSS/emtp': EMTResult,
    'function/CloudPSS/emtps': EMTResult,
    'function/CloudPSS/sfemt': EMTResult,
    'function/CloudPSS/power-flow': PowerFlowResult,
    'function/CloudPSS/ies-simulation': IESResult,
    'function/CloudPSS/ies-optimization': IESResult,
    'function/ies/ies-optimization': IESResult,
    'function/CloudPSS/three-phase-powerFlow': PowerFlowResult,
    'function/ies/ies-simulation': IESLabSimulationResult,
    'function/ies/ies-gmm':IESLabTypicalDayResult,
    'function/CloudPSS/ieslab-simulation': IESLabSimulationResult,
    'function/CloudPSS/ieslab-gmm':IESLabTypicalDayResult,
    'function/CloudPSS/ieslab-gmm-opt':IESLabTypicalDayResult,
    'function/CloudPSS/ieslab-optimization': IESResult,
}

@deprecated(version='4.0', reason="该类将在 6.0 版本移除，请使用 Job 类代替")
class Runner(Generic[T]):
    def __init__(self, id,taskId, name, job, config, revision, modelRid, policy,
                 **kwargs):
        self.id = id
        self.taskId = taskId
        self.db = Storage(taskId, name, job, config, revision, modelRid)
        rid =job['rid'].replace('job-definition/','function/').replace('/cloudpss/','/CloudPSS/')
        resultClass = kwargs.get('RESULT_DB', None)
        if resultClass is not None:
            result = resultClass
        else:
            result = RESULT_DB.get(rid, Result)
        self.result: T = result(self.db)
        self.receiver = kwargs.get('receiver', None)

    def __listenStatus(self):
        if self.receiver is None:
            return False
        if self.receiver.status() == -1:
            raise Exception(self.receiver.error)
        return self.receiver.isOpen

    def status(self):
        """
        运行状态
        :return: 运行状态  0/1/-1 1 表示正常结束，0 表示运行中， -1 表示数据接收异常


        >>>> runner.status()  
        """
        if self.receiver is None:
            raise Exception('not find receiver')
        time.sleep(0)
        return self.receiver.status()

    def __listen(self, **kwargs):
        receiver = kwargs.get('RECEIVER', 'default')
        if type(receiver) is str:
            if receiver not in RECEIVER:
                receiver = RECEIVER['default']
            else:
                receiver = RECEIVER[receiver]
        if receiver is None:
            raise Exception('not find receiver')
        self.receiver = receiver(self.taskId, self.db, **kwargs)
        self.receiver.connect()
    def statusCode(self):
        query="mutation($_a:JobInput!){job(input:$_a){status}}"
        variables= {
            "_a": {
                "id": self.jobId,
            }
        }

        return graphql_request(query,variables=variables)

    def terminate(self):
        """
        结束当前运行的算例

        """
        self.abort(0)
    def abort(self,timeout=3):
        """
        结束当前运行的算例

        """
        query = '''mutation ($input: AbortJobInput!) {
            job: abortJob(input: $input) {
                id
                status
            }
        }
        '''
        variables = {
            'input': {
                'id': self.taskId,
                'timeout': timeout
            }
        }
        graphql_request(query, variables)


    @staticmethod
    def __createJobVariables(job, config, revisionHash, rid, policy, **kwargs):
        # 处理policy字段
        if policy is None:
            policy = {}
            if policy.get("tres", None) is None:
                policy["tres"] = {}
            policy["queue"] = job["args"].get("@queue", 1)
            policy["priority"] = job["args"].get("@priority", 0)
            tres = {"cpu": 1, "ecpu": 0, "mem": 0}
            tresStr = job["args"].get("@tres", "")
            for t in re.split("\s+", tresStr):
                if t == "":
                    continue
                k, v = t.split("=")
                tres[k] = float(v)  # type: ignore
            policy["tres"] = tres
        function = job["rid"].replace("job-definition/cloudpss/", "function/CloudPSS/")
        implement = kwargs.get("implement", kwargs.get("topology", None))
        debug = job["args"].get("@debug", None )
        debugargs={}
        if debug is not None:
            parsed = parse_debug_args(debug)
            if parsed is not None:
                debugargs = parsed
            # t= [ i.split('=') for i in re.split(r'\s+',debug) if i.find('=')>0]
            # for i in t:
            #     debugargs[i[0]]=i[1]
    
        context= [
            function,
            
            f"model/@sdk/{str(int(time.time() * random.random()))}",
        ]
        if rid != '':
            context.append(rid)
        
        PARENT_JOB_ID =kwargs.get("PARENT_JOB_ID",None)
        if PARENT_JOB_ID is not None:
            context.append(f"job/parent/{PARENT_JOB_ID}")
        variables = {
            "input": {
                "args": {
                    **job["args"],
                    "_ModelRevision": revisionHash,
                    "_ModelArgs": config["args"],
                    "implement":implement
                },
                "context": context,
                "policy": policy,
                "debug":debugargs
            }
        }
        return variables
    @staticmethod
    def create(revisionHash,
               job,
               config,
               name=None,
               rid='',
               policy=None,
               **kwargs):
        '''
            创建一个运行任务

            :params: revision 项目版本号
            :params: job 调用仿真时使用的计算方案，为空时使用项目的第一个计算方案
            :params: config 调用仿真时使用的参数方案，为空时使用项目的第一个参数方案
            :params: name 任务名称，为空时使用项目的参数方案名称和计算方案名称
            :params: rid 项目rid，可为空

            :return: 返回一个运行实例

            >>> runner = Runner.runRevision(revision,job,config,'')
        '''


        query = '''mutation($input:CreateJobInput!){job:createJob(input:$input){id input output status position}}'''
        variables = Runner.__createJobVariables(job, config, revisionHash, rid,policy, **kwargs)
        r = graphql_request(query, variables)
        if 'errors' in r:
            raise Exception(r['errors'])
        messageId = r['data']['job']['output']
        id = r['data']['job']['id']
        runner = Runner(id,messageId, name, job, config, revisionHash, rid,
                        policy, **kwargs)

        event = threading.Event()
        thread = threading.Thread(target=runner.__listen, kwargs=kwargs)
        thread.setDaemon(True)
        thread.start()

        while not runner.__listenStatus():
            time.sleep(0.1)

        return runner

    

class HttpRunner(Runner[T]):

    def __init__(self, job, simulationId, **kwargs):
        self.simulationId = simulationId
        self.job = job
        self.__taskId = self.__getLastTask()
        result = IES_LAB_RESULT.get(job.get('rid', ''), IESLabPlanResult)
        self.result: T = result(self.simulationId, self.__taskId,
                                **kwargs)  # type: ignore

    def __getLastTask(self):
        r = request('GET',
                    'api/ieslab-plan/taskmanager/getSimuLastTasks',
                    params={'simuid': self.simulationId})
        result = json.loads(r.text)
        return result['data'].get('task_id', None)

    def status(self):
        if self.__taskId is None:
            return False
        return self.result.status()  # type: ignore
    
class DSLabRunner(Runner[T]):
    def __init__(self, job, simulationId, **kwargs):
        self.simulationId = simulationId
        self.job = job
        result = DS_LAB_RESULT.get(job.get('rid', ''), DSLabResult)
        self.result: T = result(self.simulationId, **kwargs)

    def status(self):
        return self.result.status()

class HttpOPTRunner(Runner[T]):

    def __init__(self, job, simulationId, **kwargs):
        self.simulationId = simulationId
        self.job = job
        self.__taskId = self.__getLastTask()
        result = IES_LAB_OPT_RESULT.get(job.get('rid', ''), IESLabOptResult)
        self.result: T = result(self.simulationId, self.__taskId,
                                **kwargs)  # type: ignore

    def __getLastTask(self):
        r = request('GET',
                    'api/ieslab-opt/taskmanager/getSimuLastTasks',
                    params={'simuid': self.simulationId})
        result = json.loads(r.text)
        return result['data'].get('task_id', None)

    def status(self):
        if self.__taskId is None:
            return False
        return self.result.status()  # type: ignore