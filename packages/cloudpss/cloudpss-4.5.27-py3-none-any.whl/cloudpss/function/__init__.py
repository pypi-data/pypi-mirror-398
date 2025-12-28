from .job import Job
from ..utils import request
from .function import Function
from .functionExecution import FunctionExecution
import json
from deprecated import deprecated

__all__ = ['Function', 'Job', 'FunctionExecution']


def createJob():
    pass


@deprecated(
    version='3.0',
    reason="该类将在 5.0 版本移除，请使用 cloudpss.currentJob() 方法代替",
)
def currentJob():
    job = Job.current()
    job.message(
        "DeprecationWarning: Call to deprecated function (or staticmethod) cloudpss.function.currentJob(). (该类将在 5.0 版本移除，请使用 cloudpss.currentJob() 方法代替",
        level='warning')
    return job
    pass


def currentExecutor():
    """
        获取表示当前执行的 FunctionExecution 单例
    """
    return FunctionExecution.current()


def fetch(rid):
    """
        获取函数
    """
    query = """
        query ($rid:ResourceId!) {
                
            function(rid:$rid) {
                rid,
                documentation
                parameters
                implementType
                implement
                configs
                context
                name
                description
                type
                owner
                key
                executor
            }
        }
    """
    payload = {
        'query': query,
        'variables': {
            'rid': rid,
        }
    }
    r = request('POST', 'graphql', data=json.dumps(payload))
    data = json.loads(r.text)
    return Function(data['data']['function'])


def fetchMany(name=None, pageSize=10, pageOffset=0):
    pass
