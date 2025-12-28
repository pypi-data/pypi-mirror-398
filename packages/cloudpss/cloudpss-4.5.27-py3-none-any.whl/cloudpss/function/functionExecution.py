import os

import json
import signal
import sys
from ..utils import MatlabDataEncoder
import threading
import queue


class EventSample(object):
    def __init__(self):
        self.__eventHandlerSample = []

    def __iadd__(self, EventHandler):
        self.__eventHandlerSample.append(EventHandler)
        return self

    def __isub__(self, EventHandler):
        self.__eventHandlerSample.remove(EventHandler)
        return self

    def __call__(self, *args, **kwargs):
        for [eventHandlerSample, eventHandlerArgs,
             eventHandlerKwargs] in self.__eventHandlerSample:
            eventHandlerSample(*eventHandlerArgs, **eventHandlerKwargs)

class EventInput(object):
    def __init__(self):
        self.__eventHandlerSample = []

    def __iadd__(self, EventHandler):
        self.__eventHandlerSample.append(EventHandler)
        return self

    def __isub__(self, EventHandler):
        self.__eventHandlerSample.remove(EventHandler)
        return self

    def __call__(self, *args, **kwargs):
        for [eventHandlerSample] in self.__eventHandlerSample:
            # 调用事件处理程序
            if eventHandlerSample:
                eventHandlerSample(*args, **kwargs)
class Args(dict):
    """
        参数类
    """
    def __getattr__(self, key):
        """__getattr__
        """
        return self[key]


class FunctionExecution(object):

    _current = None
    """ 
        FunctionExecution
    """
    def _on_abort(self, frame, sigNum):
        if not self._aborted:
            self._aborted = True
            self.__abortedEvents()

    @staticmethod
    def current():
        """
        获取表示当前执行的 FunctionExecution 单例
        """
        jobId = os.environ.get('CLOUDPSS_JOB_ID', None)
        functionId = os.environ.get('CLOUDPSS_FUNCTION_ID', None)
        executorId = os.environ.get('CLOUDPSS_EXECUTOR_ID', None)
        executorName = os.environ.get('CLOUDPSS_EXECUTOR_NAME', None)
        executorVersion = os.environ.get('CLOUDPSS_EXECUTOR_VERSION', None)
        apiUrl = os.environ.get('CLOUDPSS_API_URL', None)
        gqlUrl = os.environ.get('CLOUDPSS_GQL_URL', None)
        homeUrl = os.environ.get('CLOUDPSS_HOME_URL', None)
        jobToken = os.environ.get('CLOUDPSS_JOB_TOKEN', None)
        functionToken = os.environ.get('CLOUDPSS_FUNCTION_TOKEN', None)
        current = FunctionExecution(id=jobId,
                                    functionId=functionId,
                                    executorId=executorId,
                                    executorName=executorName,
                                    executorVersion=executorVersion,
                                    apiUrl=apiUrl,
                                    gqlUrl=gqlUrl,
                                    homeUrl=homeUrl,
                                    token=jobToken,
                                    functionToken=functionToken)
        args = FunctionExecution.__loadArgs()
        current.args = args
        FunctionExecution._current = current
        return current

    def __init__(self, **kwargs):
        self.id = kwargs.get('id', None)
        self.functionId = kwargs.get('functionId', None)
        self.executorId = kwargs.get('executorId', None)
        self.executorName = kwargs.get('executorName', None)
        self.executorVersion = kwargs.get('executorVersion', None)
        self.apiUrl = kwargs.get('apiUrl', None)
        self.gqlUrl = kwargs.get('gqlUrl', None)
        self.homeUrl = kwargs.get('homeUrl', None)
        self.token = kwargs.get('token', None)
        self.functionToken = kwargs.get('functionToken', None)
        self.__abortedEvents = EventSample()
        self.__inputEvents = EventInput()
        self._args = None
        self.__input_thread = None
        signal.signal(signal.SIGINT, self._on_abort)

    @property
    def args(self):
        return self._args

    @args.setter
    def args(self, val):
        self._args = val

    @staticmethod
    def __listObj2Array(data):
        arr=[]
        for item in data:
            if type(item) is list:
                arr.append(FunctionExecution.__listObj2Array(item))
            elif type(item) is dict and ('ɵid' in item or '?id' in item ):
                a = list(range(len(item)-1))
                for k, v in item.items():
                    if k == 'ɵid' or k == '?id':
                        continue
                    k = int(k)
                    if type(v) is list:
                        a[k] = FunctionExecution.__listObj2Array(v)
                    else:
                        a[k] = v
                arr.append(a)       
            else:
                arr.append(item)
        return arr
    @staticmethod
    def __loadArgs():
        """加载当前任务参数

        Returns:
            dict: 任务参数
        """
        args = Args()
        for k, v in os.environ.items():
            if k.startswith('CLOUDPSS_JOB_ARG-'):
                s = k.split('-')
                key = bytes.decode(bytes.fromhex(s[1]))
                data = json.loads(v)
                
                if type(data) is list:
                    data = FunctionExecution.__listObj2Array(data)
                
                args[key] = data
        return args

    def feedDog(self):
        """
            通知看门狗，当前程序还在运行，当程序 30s 内没有输出时，执行器将直接 kill 运行脚本
        """
        print("", flush=True)

    _aborted = False
    '''
    是否已取消当前任务

    当任务被取消时，将调用 on_abort 回调，已取消的任务会有 5s 时间用于清理现场并使用 {@link exit} 安全退出，

    否则执行器将直接终止运行脚本，并标记状态为 `'timed_out'`

    '''

    @property
    def aborted(self):
        return self._aborted

    def on_abort(self, func, args=[], kwargs={}):
        """
            监听前台的终止事件

            :params func 响应后的回调函数
            :params args 回调函数参数
            :params kwargs 回调函数参数
        """
        if func is not None:
            if self._aborted:
                func(*args, **kwargs)
            else:
                self.__abortedEvents += [func, args, kwargs]

    def exit(self, code):
        '''
            结束任务
            
            当任务未被取消时，分别被标记为 `'resolved'` 和 `'rejected'`；
            当任务被取消时，分别被标记为 `'aborted'` 和 `'rejected'`。
            
            调用此函数将导致进程直接终止，调用前请完成清理工作。
            
            :param code 程序退出码，运行成功返回 0，否则返回非 0
        '''
        sys.exit(code)

    def input_thread(self):
        while True:
            user_input = input()
            self.__inputEvents(user_input)
            
    def on_input(self, func):
        """
            监听input事件

            :params func 响应后的回调函数
        """
        if self.__input_thread is None:
            self.__input_thread = threading.Thread(target=self.input_thread, args=())
            self.__input_thread.start()
            self.log('cloudpss input stream is ready', 'debug')
        self.__inputEvents += [func]
        
    def print(self, data):
        print(json.dumps(data, cls=MatlabDataEncoder)+'\n', flush=True)

    def log(self, content, level='info', html=False, key=None):
        '''
            发送日志消息

            :param content 日志内容

            :param level 日志级别，可选值为 `'critical'`、`'error'`、`'warning'`、`'info'`、`'verbose'`、`'debug'`

            :param html 是否为 HTML 格式

            :param key 消息 key，用于在多个消息中引用同一消息实体，以便进行更新，或将指定 key 的消息放入容器

        '''
        self.print({
            "key": key,
            "version": 1,
            "verb": "replace",
            "type": "log",
            "data": {
                "level": level,
                'content': str(content),
                "html": html
            }
        })

    def container(self,
                  items=[],
                  layout={
                      'type': 'tabs',
                      'position': 'top'
                  },
                  key=None):
        '''
            
            发送分组消息

            :param items 分组成员，如 `[{title: 'item1', placeholder: 'Data loading', html: false, query: {type: 'message', key: 'item-1'}}]`

            :param layout 分组布局，如无特殊需求请直接使用 {@link tabsContainer} 和 {@link gridContainer}

            :param key 消息 key，用于在多个消息中引用同一消息实体，以便进行更新，或将指定 key 的消息放入容器

            @see {@link gridContainer}

            @see {@link tabsContainer}
    
        '''
        self.print({
            "key": key,
            "version": 1,
            "verb": "create",
            "type": "container",
            "data": {
                "layout": layout,
                "items": items
            }
        })

    def tabsContainer(self, items=[], position='top', key=None):
        '''
            发送 tabs 布局分组消息
        
            tabs 布局中，items[].title 为 tab 的标题
    
            :param items 分组成员，如 `[{'title': 'tab1', 'placeholder': 'Data loading', 'html': false, 'query': {'type': 'message', 'key': 'item-1'}}]`
            :param position tab 位置
            :param key 消息 key，用于在多个消息中引用同一消息实体，以便进行更新，或将指定 key 的消息放入容器
            @example
                >>> FunctionExecution.current.tabsContainer([
                        { 'title': 'tab1', 'placeholder': 'Data loading', 'html': false, 'query': { 'type': 'message', key: 'message-key-1' } },
                        { 'title': 'tab2', 'placeholder': 'Data loading', 'html': false, 'query': { 'type': 'message', 'key': 'message-key-2' } },
                    ])
                    #later
                    FunctionExecution.current.log('Content of tab1', 'info', false, 'message-key-1')
                    FunctionExecution.current.log('Content of tab2', 'info', false, 'message-key-2')
            @see {@link container}
            @see {@link gridContainer}
        '''
        self.container(items, {'type': 'tabs', 'position': position}, key)

    def gridContainer(
            self,
            item=[],
            grid="'item1 . item2' 1fr 'item1 item3 item4' 1fr / 1fr auto 2fr",
            key=None):
        '''
            发送 grid 布局分组消息

            *
            grid 布局中，items[].title 为 grid-area 名称
            *

            :param items 分组成员，如 `[{title: 'item1', placeholder: 'Data loading', html: false, query: {type: 'message', key: 'item-1'}}]`

            :param grid grid 布局说明，如 `'item1 . item2' 1fr 'item1 item3 item4' 1fr / 1fr auto 2fr`，见 https://developer.mozilla.org/en-US/docs/Web/CSS/grid-template

            :param key 消息 key，用于在多个消息中引用同一消息实体，以便进行更新，或将指定 key 的消息放入容器
            
            @example
                >>> FunctionExecution.current.gridContainer([
                        { 'title': 'item1', 'placeholder': 'Data loading', 'html': False, 'query': { 'type': 'message', 'key': 'message-key-1' } },
                        { title: 'item2', placeholder: 'Data loading', html: False, query: { type: 'message', key: 'message-key-2' } },
                        { title: 'item3', placeholder: 'Data loading', html: False, query: { type: 'message', key: 'message-key-3' } },
                    ], `'item1 item2' 1fr 'item3 item3' 2fr / 1fr 2fr`)
                    # later
                    FunctionExecution.current.log('Content of item1', 'info', False, 'message-key-1')
                    FunctionExecution.current.log('Content of item2', 'info', False, 'message-key-2')
                    FunctionExecution.current.log('Content of item3', 'info', False, 'message-key-3')
                    # You'll see the following grid:
                    #    1fr        2fr
                    # | item1 | C.of item2 | 1fr
                    # |       Content      | 2fr
                    # |      of item3      |
            @see {@link container}
            @see {@link tabsContainer}
        '''
        self.container(item, {'type': 'grid', 'grid': grid}, key)

    def progress(self, value=0, title='', key='progress-1'):
        '''
            发送进度信息
            
            :param value 当前进度值，取值范围 0~1

            :param title 进度标题

            :param key 消息 key，用于在多个消息中引用同一消息实体，以便进行更新，或将指定 key 的消息放入容器
        '''
        self.print({
            "key": key,
            "version": 1,
            "verb": "replace",
            "type": "progress",
            "data": {
                "value": value,
                "title": title
            }
        })

    def table(self, columns=[], title='', key=None, verb='replace'):
        '''
            发送表格信息
        
            :param columns 按列分组的表格内容

            :param title 表格标题

            :param key 消息 key，用于在多个消息中引用同一消息实体，以便进行更新，或将指定 key 的消息放入容器

            :param verb 特殊谓词，使用 `'append'` 和 `'prepend'` 在已有表格上追加或插入内容

            @example
            >>> FunctionExecution.current.table([
                    { 'name': 'col1', 'type': 'text', 'data': ['a', 'b', 'c'] },
                    { 'name': 'col2', 'type': 'number', 'data': [1, 2, 3] },
                ], 'My Data Table', 'table-1')
                #later
                FunctionExecution.current.table([
                    { 'name': 'col1', 'type': 'text', 'data': ['d'] },
                    { 'name': 'col2', 'type': 'number', 'data': [4] },
                ], 'My Data Table - Updated', 'table-1', 'append')
        '''
        self.print({
            "key": key,
            "version": 1,
            "verb": verb,
            "type": "table",
            "data": {
                "columns": columns,
                "title": title
            }
        })

    def __flat_map(self, data, target=None, prefix=""):
        if target is None:
            target = {}
        for k, v in data.items():
            if type(v) is dict:
                self.__flat_map(v, target, prefix + k + ".")
            else:
                target[prefix + k] = v
        return target

    def __plotlyDataToTrace(self, data):

        result = self.__flat_map(data)
        return result

    def plot(self, traces=[], layout={}, title='', key=None, verb='replace'):
        '''
            发送图表信息
        
            :param traces 图表数据

            :param layout 图表坐标轴信息

            :param title 图表标题

            :param key 消息 key，用于在多个消息中引用同一消息实体，以便进行更新，或将指定 key 的消息放入容器

            :param verb 特殊谓词，使用 `'append'` 和 `'prepend'` 在已有图表上追加或插入内容，使用 `'update'` 进行局部更新

            @example
                >>> FunctionExecution.current.plot([
                { 'name': 'trace1', 'type': 'scatter', 'x': [1, 2, 3], 'y': [1, 2, 3] },
                    { 'name': 'trace2', 'type': 'bar', 'x': [1, 2, 3], 'y': [1, 2, 3] },
                ], {
                    'xaxis': { 'title': 'x' },
                    'yaxis': { 'title': 'y' },
                }, 'My Plot', 'plot-1')
                #later
                FunctionExecution.current.plot([
                    { 'x': [4], 'y': [4] },
                    { 'x': [4], 'y': [4] },
                ], {}, 'My Plot - Updated', 'plot-1', 'append')
            @see traces 参见 {@link https://plotly.com/javascript/reference/index/ plotly} 文档
        '''

        result = {
            'key': key,
            'version': 1,
            'verb': verb,
            'type': 'plot',
            'data': {
                'title': title,
                'traces':
                [self.__plotlyDataToTrace(trace) for trace in traces],
                'layout': layout,
            }
        }
        self.print(result)
        
    def custom(self, data, key=None,verb='replace'):
        result = {
            'key': key,
            'version': 1,
            'verb': verb,
            'type': 'custom',
            'data': data
        }
        self.print(result)