import json
from collections import namedtuple
from typing import Any, Dict, List, Union
import copy

PARSER_STATUS_TEXT = 0
PARSER_STATUS_EXPRESSION_SIMPLE = 1
PARSER_STATUS_EXPRESSION_COMPLEX = 2

def is_identifier_char(char):
    char_code = ord(char)
    return ((char_code >= 97 and char_code <= 122) or
            (char_code >= 65 and char_code <= 90) or
            (char_code >= 48 and char_code <= 57) or
            char_code == 95)

INTERPOLATION_CHAR = '$'
# INTERPOLATION_EXPRESSION_START = '{'
INTERPOLATION_EXPRESSION_START = ['{', '[', '<', '(']
# INTERPOLATION_EXPRESSION_END = '}'
INTERPOLATION_EXPRESSION_END = ['}', ']', '>', ')']

def parse_interpolation_impl(template, start, length):
    templates = []
    values = []
    current_template = ''
    current_value = ''
    expression_complex_depth = 0
    status = PARSER_STATUS_TEXT
    end = start + length - 1
    complexExpressionStartType = -1
    i = start
    while i <= end:
    # for i in range(start, end + 1):
        
        if status == PARSER_STATUS_TEXT:
            next_interpolation_char = template.find(INTERPOLATION_CHAR, i)
            if next_interpolation_char < 0 or next_interpolation_char >= end:
                current_template += template[i:end + 1]
                break
            current_template += template[i:next_interpolation_char]
            next_char = template[next_interpolation_char + 1]
            i = next_interpolation_char
            # if next_char == INTERPOLATION_CHAR:
            #     current_template += INTERPOLATION_CHAR
            #     i += 1
            #     continue
            # if next_char == INTERPOLATION_EXPRESSION_START:
            
            complexExpressionStartType= INTERPOLATION_EXPRESSION_START.index(next_char) 
            if complexExpressionStartType>=0:
                templates.append(current_template)
                current_template = ''
                status = PARSER_STATUS_EXPRESSION_COMPLEX
                expression_complex_depth = 1
                i += 2
                continue
            if is_identifier_char(next_char):
                templates.append(current_template)
                current_template = ''
                current_value = next_char
                status = PARSER_STATUS_EXPRESSION_SIMPLE
                i += 2
                continue
            current_template += INTERPOLATION_CHAR
            continue
        
        char = template[i]
        if status == PARSER_STATUS_EXPRESSION_SIMPLE:
            if is_identifier_char(char):
                current_value += char
                i += 1
                continue
            values.append(current_value)
            current_value = ''
            status = PARSER_STATUS_TEXT
            i -= 1
            continue
        
        if status == PARSER_STATUS_EXPRESSION_COMPLEX:
            if char == INTERPOLATION_EXPRESSION_START[complexExpressionStartType]:
                expression_complex_depth += 1
            elif char == INTERPOLATION_EXPRESSION_END[complexExpressionStartType]:
                expression_complex_depth -= 1
                if expression_complex_depth == 0:
                    values.append(current_value.strip())
                    current_value = ''
                    status = PARSER_STATUS_TEXT
                    i += 1
                    continue
            current_value += char
            i += 1
            continue
    if status == PARSER_STATUS_TEXT:
        templates.append(current_template)
    elif status == PARSER_STATUS_EXPRESSION_SIMPLE:
        values.append(current_value)
        templates.append('')
    else:
        raise ValueError('Unexpected end of input')
    
    return {
        'type': 'interpolation',
        'templates': templates,
        'values': values,
    }
    
# 是否为 ArrayBuffer
def is_array_buffer(value: Any) -> bool:
    return isinstance(value, (memoryview, bytearray))

# 是否为 Error
def is_error(value: Any) -> bool:
    return isinstance(value, Exception)


def parse_template(template: str) -> Any:
    if not template:
        return ''
    if template.startswith('='):
        return {
            'type': 'formula',
            'value': template[1:].strip(),
        }
    if template.startswith('$'):
        result = parse_interpolation_impl(template, 1, len(template)-1)
        if len(result['templates']) == 0:
            return result['templates'][0]
        return result        
    return template
# KNOWN_ERRORS = [EvalError, RangeError, ReferenceError, SyntaxError, TypeError, URIError]

# 模板序列号
seq = 0

# 创建模板
class TemplateCompiler:
    def __init__(self, template: Any, options: Dict[str, Any]):
        self.template = template
        self.options = options
        self.params = {}
        self.copyable = []

    # 构建求值
    def build_eval(self, expression: str, type_: str) -> str:
        evaluator = self.options['evaluator']
        if 'evaluator' not in self.params:
            self.params['evaluator'] = evaluator.get('inject',None)
        return evaluator['compile'](expression, type_)

    # 构建字符串
    def build_string(self, str_: str) -> Union[str, bool]:
        parsed = parse_template(str_)
        if isinstance(parsed, str):
            return json.dumps(parsed), False
        if parsed['type'] == 'formula':
            return self.build_eval(parsed['value'], parsed['type']), True
        result = ''
        for i in range(len(parsed['templates'])):
            if parsed['templates'][i]:
                result += (result and '+' or '') + json.dumps(parsed['templates'][i])
            if i < len(parsed['values']):
                if not result:
                    result = '""'
                result += '+' + self.build_eval(parsed['values'][i], parsed['type'])
        return result, True

    # 构建 Error
    def build_error(self, err: Exception) -> str:
        constructor="Error"
        if err.__class__.__name__ == constructor:
            return f'new {constructor}({self.build_string(err.message)[0]})'
        return f'Object.assign(new {constructor}({self.build_string(err.message)[0]}), {{name: {self.build_string(err.name)[0]}}})'

    # 构建数组
    def build_array(self, arr: List[Any]) -> str:
        return f'[{", ".join(self.build_value(v) for v in arr)}]'

    # 构建 ArrayBuffer
    def build_array_buffer(self, buffer: Union[memoryview, bytearray]) -> str:
        self.copyable.append(buffer[:])
        return f'copyable[{len(self.copyable) - 1}][:]'

    # 构建 ArrayBufferView
    def build_array_buffer_view(self, view: memoryview) -> str:
        self.copyable.append(view.tobytes())
        return f'new {view.__class__.__name__}(copyable[{len(self.copyable) - 1}][:])'

    # 构建对象
    def build_object(self, obj: Dict[str, Any]) -> str:
        result = ''
        for key, value in obj.items():
            if result:
                result += ',\n'
            if self.options['objectKeyMode'] == 'ignore':
                result += json.dumps(key)
            else:
                e, is_expression = self.build_string(key)
                if is_expression:
                    result += f'[{e}]'
                else:
                    result += e
            result += ':'
            result += self.build_value(value)
        return '{' + result + '}'

    # 构建值
    def build_value(self, value: Any) -> str:
        if value is None:
            return 'null'
        if value is True:
            return 'True'
        if value is False:
            return 'False'
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, str):
            return self.build_string(value)[0]
        if isinstance(value, Exception):
            return self.build_error(value)
        if isinstance(value, list):
            return self.build_array(value)
        if is_array_buffer(value):
            return self.build_array_buffer(value)
        if isinstance(value, memoryview):
            return self.build_array_buffer_view(value)
        if isinstance(value, dict):
            return self.build_object(value)
        raise ValueError(f'Unsupported value: {type(value)}')

    # 构建模板
    def build(self) -> Any:
        global seq
        source = self.build_value(self.template)
        if self.copyable:
            self.params['copyable'] = self.copyable
        params = list(self.params.items())
        try:
            result = eval(f'lambda context: ({source})')
            result.source = source
            return result
        except Exception as e:
            raise ValueError(f'Failed to compile template: {source}\n{str(e)}')



def template(templates,options={}):
    def compile_template(expression, type):
        if type == 'formula':
            return f'copy.deepcopy(context.get({json.dumps(expression)},None))'
        elif type == 'interpolation':
            return f"context.get({json.dumps(expression)},'')"
        raise ValueError(f'Unsupported type: {type}')
    opt = {
        'objectKeyMode': 'template',
        'evaluator':{
            'compile':compile_template
        },
        **options
    }
    return TemplateCompiler(templates, opt).build()



if __name__ == "__main__":
    
    message =[1, 1, {'component_load_5_无功功率': [0], 'component_load_5_有功功率': [0], 'time': ['placeholder']}, {'data': {'title': '负荷5功率(kW)', 'traces': [{'name': '有功功率', 'type': 'scatter', 'x': '=time', 'y': '=component_load_5_有功功率'}, {'name': '无功功率', 'type': 'scatter', 'x': '=time', 'y': '=component_load_5_无功功率'}], 'xAxis': {'title': 'time'}, 'yAxis': {'title': '功率(kW)'}}, 'key': '/component_load_5_功率(kW)', 'type': 'plot', 'verb': 'append', 'version': 1}]
    message =[782312650, 1, {'t': [], 'd5': [], 'd8': [], 'd9': [], 'v0': 'append', 'd6': [], 'v1': 'append'}, {'key': 'plot-1', 'version': 1, 'type': 'plot', 'verb': '=v0', 'data': {'title': '整流侧交流电流', 'layout': {'xaxis.range': '=xr0', 'xaxis.autorange': False}, 'traces': [{'name': 'Ia', 'type': 'scattergl', 'yaxis': 'y', 'x': '=t', 'y': '=d5'}, {'name': 'Ib', 'type': 'scattergl', 'yaxis': 'y', 'x': '=t', 'y': '=d8'}, {'name': 'Ic', 'type': 'scattergl', 'yaxis': 'y', 'x': '=t', 'y': '=d9'}]}}, {'key': 'plot-2', 'version': 1, 'type': 'plot', 'verb': '=v1', 'data': {'title': 'A相上桥臂电容电压', 'layout': {'xaxis.range': '=xr1', 'xaxis.autorange': False}, 'traces': [{'name': 'Vc', 'type': 'scattergl', 'yaxis': 'y', 'x': '=t', 'y': '=d6'}]}}]
    id =message[0]
    
    templates=message[3:]
    
    x= template(templates)
    
    values=[782312650, 1, {'t': [0.009999999999999967, 0.010999999999999961, 0.011999999999999955, 0.012999999999999949, 0.013999999999999943, 0.014999999999999937, 0.015999999999999945, 0.016999999999999973, 0.018000000000000002, 0.01900000000000003], 'd5': [0.07483153188510672, 0.09331340076657475, 0.10060354339781043, 0.08143820164529898, 0.06475492808815062, 0.03988870901471444, 0.017856545584211857, -0.00022077163899950848, -0.01795813197603053, -0.02080189617972792], 'd8': [-0.1375203178103291, -0.10701993395081587, -0.08370609309571676, -0.04136648742407317, -0.009632672956318231, 0.012930786595120338, 0.023576938091071184, 0.027067414097930786, 0.02056424854512571, 0.0032354404004249202], 'd9': [0.06256431502056557, 0.013651990940627457, -0.01694762608987588, -0.039966571588256096, -0.055297953120400006, -0.05275643941375492, -0.04137165007706727, -0.02687559851684142, -0.0025904403473839465, 0.017612961883902756], 'd6': [11.089656437630765, 11.090168556304207, 11.09058932753887, 11.090721058893884, 11.090593484855583, 11.090478358824114, 11.090135588005115, 11.089385203292103, 11.088182236357547, 11.086255229686746], 'xr0': [0, 2], 'xr1': [0, 2]}]
    
    print(x)
    
    data= values[2]
    s=x(data)
    
    print(s)