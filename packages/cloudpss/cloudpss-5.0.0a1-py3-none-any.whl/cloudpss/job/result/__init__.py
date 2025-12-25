from .IESResult import IESResult
from .result import Result
from .EMTResult import EMTResult,VirtualInput
from .PowerFlowResult import PowerFlowResult
from .IESLabSimulationResult import IESLabSimulationResult
from .IESLabTypicalDayResult import IESLabTypicalDayResult
from ..messageStreamReceiver import MessageStreamReceiver
from ..messageStreamSender import MessageStreamSender
__all__ = [
    'Result','EMTResult','PowerFlowResult','IESLabSimulationResult','IESResult','IESLabTypicalDayResult','MessageStreamReceiver','MessageStreamSender',"VirtualInput"
]

RESULT = {
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
    'function/CloudPSS/ieslab-optimization': IESResult,
    'function/CloudPSS/ieslab-gmm-opt':IESLabTypicalDayResult,
}


def getResultClass(rid: str) -> Result:
    """
    获取仿真结果视图

    :param rid: 仿真任务的 rid
    :param db: 仿真任务的数据库

    :return: 仿真结果视图
    """
    return RESULT.get(rid, Result)