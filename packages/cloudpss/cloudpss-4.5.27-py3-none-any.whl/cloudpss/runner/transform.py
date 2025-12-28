import re
import os
import io
import datetime
import time
COLOR_LIST = [
    'var(--spectrum-global-color-celery-700)',
    'var(--spectrum-global-color-chartreuse-700)',
    'var(--spectrum-global-color-yellow-700)',
    'var(--spectrum-global-color-magenta-700)',
    'var(--spectrum-global-color-fuchsia-700)',
    'var(--spectrum-global-color-purple-700)',
    'var(--spectrum-global-color-indigo-700)',
    'var(--spectrum-global-color-seafoam-700)',
    'var(--spectrum-global-color-red-700)',
    'var(--spectrum-global-color-orange-700)',
    'var(--spectrum-global-color-green-700)',
    'var(--spectrum-global-color-blue-700)',
    'var(--spectrum-global-color-celery-400)',
    'var(--spectrum-global-color-chartreuse-400)',
    'var(--spectrum-global-color-yellow-400)',
    'var(--spectrum-global-color-magenta-400)',
    'var(--spectrum-global-color-fuchsia-400)',
    'var(--spectrum-global-color-purple-400)',
    'var(--spectrum-global-color-indigo-400)',
    'var(--spectrum-global-color-seafoam-400)',
    'var(--spectrum-global-color-red-400)',
    'var(--spectrum-global-color-orange-400)',
    'var(--spectrum-global-color-green-400)',
    'var(--spectrum-global-color-blue-400)',
    'var(--spectrum-global-color-celery-500)',
    'var(--spectrum-global-color-chartreuse-500)',
    'var(--spectrum-global-color-yellow-500)',
    'var(--spectrum-global-color-magenta-500)',
    'var(--spectrum-global-color-fuchsia-500)',
    'var(--spectrum-global-color-purple-500)',
    'var(--spectrum-global-color-indigo-500)',
    'var(--spectrum-global-color-seafoam-500)',
    'var(--spectrum-global-color-red-500)',
    'var(--spectrum-global-color-orange-500)',
    'var(--spectrum-global-color-green-500)',
    'var(--spectrum-global-color-blue-500)',
    'var(--spectrum-global-color-celery-600)',
    'var(--spectrum-global-color-chartreuse-600)',
    'var(--spectrum-global-color-yellow-600)',
    'var(--spectrum-global-color-magenta-600)',
    'var(--spectrum-global-color-fuchsia-600)',
    'var(--spectrum-global-color-purple-600)',
    'var(--spectrum-global-color-indigo-600)',
    'var(--spectrum-global-color-seafoam-600)',
    'var(--spectrum-global-color-red-600)',
    'var(--spectrum-global-color-orange-600)',
    'var(--spectrum-global-color-green-600)',
    'var(--spectrum-global-color-blue-600)',
];

class Transformer():

    def __init__(self, job):
        self.drawMetadata = None
        self.job = job
        self.firstDraw = True

    def __msg(self, data, level):
        rex = r'^\[\s*\d{1,4}\/\d{1,2}\/\d{1,4}\s+\d{2}:\d{2}:\d{2}\s*\]\s*\[(critical|warning|error|info|verbose|debug)\]\s*'
        match = re.match(rex, data, re.I | re.S)
        if match:
            data = data[len(match.group(0)):]
            level = match.group(1)
        if re.match(r'^\s*run ends!?\s*$', data, re.I | re.S):
            return {
                'type': 'terminate',
                'version': 1,
                'key': '%.9f' % time.time(),
                'data': {
                    'succeeded':
                        'resolved' if self.previousLevel != 'critical' and
                        self.previousLevel != 'error' and
                        level != 'critical' and
                        level != 'error' else 'rejected',
                },
                # 'id':id,
                'sender': 'remote',
                'when': datetime.datetime.now(),
            }
        self.previousLevel = level
        return {
            'type': 'log',
            'verb': 'create',
            'version': 1,
            'key': '%.9f' % time.time(),
            'data': {
                'level': level,
                'content': data,
            },
            # 'id':id,
            'sender': 'remote',
            'when': datetime.datetime.now()
        }

    def __draw(self, data):
        globalBegin = self.job['args']['begin_time']
        globalEnd = self.job['args']['end_time']
        plots = []
        if data is None:
            return None
        if not self.drawMetadata:

            resultData = []
            plot = {'plot-1': {
                'type': 'plot',
                'key': 'plot',
                'verb': 'create' if self.firstDraw else 'append',
                'version': 1,
                'data': {
                    'traces': resultData,
                },
                'sender': 'remote',
                'when': datetime.datetime.now()
            }}
            for key, val in data.items():
                x, y = zip(*val)
                resultData.append({
                    'name': key,
                    'type': 'scatter',
                    'x': list(x),
                    'y': list(y),
                })
            self.firstDraw = False
            return plot

        else:
            for i in range(len(self.drawMetadata)):
                plotKey = 'plot-{0}'.format(i)
                meta = self.drawMetadata[i]

                axis = None
                try:
                    if meta['type'] == 'oscilloscope':
                        if meta.get('width', None) is not None:
                            dataSample = data[meta['traces'][0]['key']]
                            if dataSample is not None:
                                end = dataSample[len(dataSample)-1][0]
                                remaining = end % float(meta['width'])
                                if remaining <= 0.000001:
                                    remaining = meta['width']
                                axis = {
                                    'range': [end - remaining, end - remaining + meta['width']]}

                    elif meta['type'] == 'moving':
                        if meta.get('width', None) is not None:
                            begin = globalBegin
                            dataSample = data[meta['traces'][0]['key']]
                            end = dataSample[len(dataSample) - 1][0]
                            begin = max(
                                float(end)-float(meta['width']), float(begin))
                            axis = {'range': [begin, end]}

                    elif meta['type'] == 'global':
                        axis = {'range': [globalBegin, globalEnd]}
                except Exception as e:
                    print(e)
                resultData = []
                plot = {
                    'type': 'plot',
                    'key': plotKey,
                    'verb': 'create' if self.firstDraw else 'append',
                    'version': 1,
                    'data': {
                        'title': meta['title'] if self.firstDraw else None,
                        'xAxis': axis,
                        'traces': resultData,
                    },
                    'sender': 'remote',
                    'when': datetime.datetime.now()
                }
                traces = meta['traces']
                for val in traces:
                    element = data.get(val['key'], None)
                    if not element:
                        resultData.append({
                            'name': val['name'],
                            'type': 'scatter',
                            'x': [],
                            'y': [],
                        })
                        continue
                    x, y = zip(*element)
                    resultData.append({
                        'name': val['name'],
                        'type': 'scatter',
                        'x': list(x),
                        'y': list(y),
                    })
                plots.append(plot)
            self.firstDraw = False
            return plots

    def __compValues(self, data, field):
        if data is None:
            return None
        components = {}
        for key, val in data.items():
            if not key.startswith('/'):
                continue
            compKey = key[1:]
            components[compKey] = {field: val}
        result = {
            'type': 'modify',
            'version': 1,
            'data': {
                'payload': {
                    'revision': {
                        'implements': {
                            'diagram': {
                                'components': components,
                            }
                        },
                    },
                },
            }
        }
        if self.job['rid'] == 'job-definition/cloudpss/power-flow':
            if field == 'args':
                result['data']['title'] = '潮流初始化断面'
                result['data']['content'] = '将潮流结果写回模型作为暂态仿真初始化断面'
            elif field == 'context':
                result['data']['title'] = '潮流可视化展示'
                result['data']['content'] = '在图纸上展示此潮流结果'
        return result

    def __status(self, data, field):
        if data is None:
            return None
        cells = {}
        for key, val in data.items():
            if not key.startswith('/'):
                continue
            compKey = key[1:]

            cells[compKey] = {field: {
                '--stroke': COLOR_LIST[int(val['color']) % len(COLOR_LIST)], 'title': val['value']}}
        result = {
            'type': 'modify',
            'version': 1,
            'data': {
                'payload': {
                    'revision': {
                        'implements': {
                            'diagram': {
                                'cells': cells,
                            }
                        },
                    },
                },
            }
        }
        if self.job['rid'] == 'job-definition/cloudpss/emtp':
            result['data']['title'] = '分网结果'
            result['data']['content'] = '在拓扑中显示分网结果'
        return result

    def transform(self, message):

        if message['cmd'] == 'msg':
            return self.__msg(message['data'], 'info')

        elif message['cmd'] == 'errormsg':
            return self.__msg(message['data'], 'error')

        elif message['cmd'] == 'terminate':
            data = message['data']
            return {
                'type': 'terminate',
                'version': 1,
                'data': {'succeeded': data.get('succeeded', True)},
            }
        elif message['cmd'] == 'message':
            data = message.data
            return {
                'type': 'log',
                'verb': 'create',
                'version': 1,
                'data': {
                    'level': data['level'],
                    'content': data['content'],
                    'html': True,
                },
                'key': '%.9f' % time.time(),
                'when': datetime.datetime.now(),

            }
        elif message['cmd'] == 'drawmeta':
            self.drawMetadata = message['data']

        elif message['cmd'] == 'draw' or message['cmd'] == 'chart':
            data = message.get('data', None)
            return self.__draw(data)

        elif message['cmd'] == 'compParams':
            data = message.get('data', None)
            if data is None:
                return None
            app = data.get('defaultApp', None)
            msg = self.__compValues(app, 'args')
            return msg
        elif message['cmd'] == 'context':
            data = message.get('data', None)
            return self.__compValues(data, 'context')
        elif message['cmd'] == 'status':
            data = message.get('data', None)
            return self.__status(data, 'style')
        return None
