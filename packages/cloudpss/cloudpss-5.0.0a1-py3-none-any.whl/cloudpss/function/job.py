import os

import json
from ..utils import request, DateTimeEncode, MatlabDataEncoder
from deprecated import deprecated


class Args(dict):
    """
    参数类
    """
    def __getattr__(self, key):
        """
            __getattr__

        """
        return self[key]


@deprecated(version='3.0', reason="该类将在 5.0 版本移除，请使用 currentExecution 类代替")
class Job(object):
    """ 
        Function Job

    """
    def __init__(self, **kwargs):
        self.id = kwargs.pop('id', None)
        self.apiUrl = kwargs.pop('apiUrl', None)
        self.executorId = kwargs.pop('executorId', None)
        self.homeUrl = kwargs.pop('homeUrl', None)
        self.version = kwargs.pop('version', None)
        self.token = kwargs.pop('token', None)
        self._args = None

    @staticmethod
    def current():
        """获取当前任务

        Returns:
            Job: 任务类

        """
        id = os.environ.get('CLOUDPSS_JOB_ID', None)
        apiUrl = os.environ.get('CLOUDPSS_API_URL', None)
        executorId = os.environ.get('CLOUDPSS_EXECUTOR_ID', None)
        homeUrl = os.environ.get('CLOUDPSS_HOME_URL', None)
        token = os.environ.get('CLOUDPSS_TOKEN', None)
        version = os.environ.get('CLOUDPSS_STUDIO_VERSION', None)
        job = Job(id=id,
                  apiUrl=apiUrl,
                  executorId=executorId,
                  homeUrl=homeUrl,
                  version=version,
                  token=token)
        args = Job.loadArgs()
        job.args = args
        return job

    @staticmethod
    def loadArgs():
        """加载当前任务参数

        Returns:
            dict: 任务参数

        """
        args = Args()
        for k, v in os.environ.items():
            if k.startswith('CLOUDPSS_JOB_ARG-'):
                s = k.split('-')
                key = bytes.decode(bytes.fromhex(s[1]))
                # print(key, v, flush=True)

                args[key] = json.loads(v)
        return args

    @property
    def args(self):
        return self._args

    @args.setter
    def args(self, val):
        self._args = val

    def feedDog(self):
        """
            通知看门狗，当前程序还在运行，当程序 30s 内没有输出时，执行器将直接 kill 运行脚本
        """
        print("", flush=True)

    def progress(self, val, key='progress-1', title=''):
        """
            发送进度信息

            :params val: float 进度值 [0-1]
            :params key: str 目标, key 相同的数据会往同一个目标写入数据
            :params title: str 进度 标题

            >>> job.progress(0.2)
        """

        result = {
            'key': key,
            'version': 1,
            'verb': 'append',
            'type': 'progress',
            'data': {
                'title': title,
                'value': val
            }
        }
        print(json.dumps(result), flush=True)

    def message(self, msg, level='info', key=None, verb='create'):
        """
            发送日志信息

            :params msg: str 消息内容
            :params level: 消息类型 默认 info 可选：'critical' | 'error' | 'warning' | 'info' | 'verbose' | 'debug'
            :params key: str 目标, key 相同的数据会往同一个目标写入数据
            :params verb: 操作类型，可选  'create' | 'replace' | 'append' | 'prepend'

            >>> job.message('info message')
            >>> job.message('error message', level='error')


            在同一个目标显示消息
            >>> job.message('message1', key='log-1')
            >>> job.message('message2', key='log-1',verb='append')

            替换目标数据
            >>> job.message('message1', key='log-1')
            >>> job.message('message2', key='log-1',verb='replace')

        """
        result = {
            'key': key,
            'version': 1,
            'verb': verb,
            'type': 'log',
            'data': {
                'level': level,
                'content': str(msg)
            }
        }
        print(json.dumps(result), flush=True)

    def plot(self, key, traces, verb='append', layout={}, **kwargs):
        """
            发送绘图消息

            :params key: 目标， key 相同数据将显示到同一个图表上
            :params traces: Array 曲线数据组，
               >>>> [{
                    'name': str,  曲线名称
                    'type': 'scatter' | 'bar'  曲线类型
                    'x' : float[]   x 轴数据
                    'y' : float[]   y 轴数据
                }]
            :params title: str 图表标题
            :params xAxis: dict 坐标轴设置
            :params yAxis: dict 坐标轴设置
                >>> {
                    'title':str,   轴标题
                    'type' : 'linear' | 'log' | 'date',  轴类型
                    'range': [number, number] | 'auto'   显示范围
                }

            :params verb: str 消息内容 可选： 'create' | 'replace' | 'append' | 'prepend' | 'update'

            >>> job.plot('plot-1',[{'name':'t1','type':'scatter','x':[1,2],'y':[3,4]}])

        """

        result = {
            'key': key,
            'version': 1,
            'verb': verb,
            'type': 'plot',
            'data': dict({'traces': traces}, **layout)
        }
        print(json.dumps(result, cls=MatlabDataEncoder), flush=True)

    def table(self, key, columns, title='', verb='append', **kwargs):
        """
            发送表格数据

            :params key: str 目标, key 相同的数据会往同一个目标写入数据

            :params columns: Array 表格的列数据组
            >>> [{
                'name': str, 列名称
                'type': 'text' | 'html' | 'number',  列类型
                'data': unknown[]  列数据
            }]
            :params title: str 图表标题
            :params verb: 操作类型，可选  'create' | 'replace' | 'append' | 'prepend'

            >>> job.table('info message')
            >>> job.table('error message', level='error')

        """

        result = {
            'key': key,
            'version': 1,
            'verb': verb,
            'type': 'table',
            'data': {
                'title': title,
                'columns': columns
            }
        }

        print(json.dumps(result, cls=MatlabDataEncoder), flush=True)

    def terminate(self, status):
        """
            发送结束消息

            :params status: 结束状态 可以选 'resolved' | 'rejected' | 'aborted' | 'timed_out'

            >>> job.terminate('resolved')
        """

        result = {
            'version': 1,
            'verb': '',
            'type': 'terminate',
            'data': {
                'status': status,
            }
        }

        print(json.dumps(result), flush=True)

    def abort(self, data):
        """
            发送中止消息

            :params data: 消息数据

            >>> job.abort({})
        """
        result = {'version': 1, 'verb': '', 'type': 'abort', 'data': data}

        print(json.dumps(result), flush=True)

    def __flat_map(self, data, target=None, prefix=""):
        if target is None:
            target = {}
        for k, v in data.items():
            if type(v) is dict:
                self.__flat_map(v, target, prefix + k + ".")
            else:
                target[prefix + k] = v
        return target

    def plotLyDataToTrace(self, data):

        result = self.__flat_map(data)
        return result

    def print(self, message):
        print(json.dumps(message, cls=DateTimeEncode), flush=True)

    def container(self, data, key=None, verb=None):
        """
            发送消息组
            :params key: 图标索引 key
            :params verb: 操作类型，可选  'create' | 'replace' | 'append' | 'prepend'
            :params data: 分组数据
            
            {
                layout?:
                    | {
                        /** 浮窗显示，title 为 anchor（如：`/design/diagram/cells/canvas_0_16`），用于决定显示的内容 */
                        type: 'float';
                    }
                    | {
                        /** tab 页方式显示，title 为 tab 的标题 */
                        type: 'tabs';
                        position: 'left' | 'right' | 'top' | 'bottom';
                    }
                    | {
                        /** grid 布局显示，title 为 grid-area 名称 */
                        type: 'grid';
                        /** CSS grid 属性，如 `'item1 . item2' 1fr 'item1 item3 item4' 1fr / 1fr auto 2fr` */
                        grid: string;
                    };
                items: Array<{
                    /** 根据 `layout.type` 具有不同的功能 */
                    title: string;
                    /** 对应 key 数据不存在时显示 */
                    placeholder: string;
                    /** placeholder 是否使用 html */
                    html: boolean;
                    /** 获取用于填充的数据的方式 */
                    query?:
                        | {
                            /** 查找指定 key 的消息填充 */
                            type: 'message';
                            key: string;
                            /** 当此属性存在时，如未找到指定消息，向调用方发送该 payload 进行查询 */
                            signal?: MessagePayload;
                        }
                        | {
                            /** 通用 web api */
                            type: 'http';
                            method: string;
                            url: string;
                            headers: Record<string, string>;
                            body: unknown;
                            /** 从响应中获取消息的方法 */
                            picker?:
                                | string[] // 从响应体的路径 pick（lodash.get）
                                | ExpressionSource<unknown>; // 通过表达式获取（可用对象 $req, $res）
                        }
                        | {
                            /** 从对象存储获取指定对象填充 */
                            type: 'object-storage';
                            hash: string;
                        }
                        | {
                            /** 从对象存储获取指定对象填充 */
                            type: 'object-storage';
                            hash: string;
                        };
                }>;
            };
            >>> job.container(data,"key-c")
        """
        result = {
            'version': 1,
            "key": key,
            'verb': verb,
            'type': 'container',
            'data': data
        }
        print(result)
        print(json.dumps(result), flush=True)

    def gridContainer(self, items, grid=None, key=None, verb=None):
        """
            发送 类型为grid 的消息组

            :params items: 需要关联的其他图表消息 {'title':标题，'placeholder': 默认显示内容，key：需要关联的图表}
            :params tabsPosition: 操作类型，可选   'top' | 'bottom'

            :params key: 图标索引 key
            :params verb: 操作类型，可选  'create' | 'replace' | 'append' | 'prepend'
        """
        itemData = []
        s = ''
        for val in items:
            itemData.append({
                'title': val['title'],
                'placeholder': val.get('placeholder', "no data"),
                "query": {
                    'type': 'message',
                    'key': val['key'],
                } if val.get('key', None) is not None else None
            })
            s = s + '"{0}" 1fr '.format(val['title'])
        s = s + "/ auto"
        grid = grid if grid is not None else s
        data = {'items': itemData, 'layout': {'type': 'grid', 'grid': grid}}

        self.container(data, key, verb)

    def tabContainer(self, items, tabsPosition='top', key=None, verb=None):
        """
            发送 类型为grid 的消息组

            :params keys: 需要关联的其他图表列表
            :params tabsPosition: 操作类型，可选  'top' | 'bottom'

            :params key: 图标索引 key
            :params verb: 操作类型，可选  'create' | 'replace' | 'append' | 'prepend'
            

        """
        itemData = []
        for val in items:
            itemData.append({
                'title': val['title'],
                'placeholder': val.get('placeholder', "no data"),
                "query": {
                    'type': 'message',
                    'key': val['key'],
                } if val.get('key', None) is not None else None
            })
        data = {
            'items': itemData,
            'layout': {
                'type': 'tabs',
                'position': tabsPosition
            }
        }
        self.container(data, key, verb)
