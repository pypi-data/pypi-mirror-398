import io
import json
import ubjson
import yaml
from yaml.dumper import SafeDumper
import gzip
import base64
import struct
import zstandard as zstd


def float32Array(_loader, node):
    data = base64.b64decode(node.value)
    return list(struct.unpack('f' * (len(data) // 4), data))


def float64Array(_loader, node):
    data = base64.b64decode(node.value)
    return list(struct.unpack('d' * (len(data) // 8), data))


def uint8Array(_loader, node):
    data = base64.b64decode(node.value)
    return list(struct.unpack('B' * (len(data) // 1), data))


def uint8ClampedArray(_loader, node):
    data = base64.b64decode(node.value)
    return list(struct.unpack('B' * (len(data) // 1), data))


def uint16Array(_loader, node):
    data = base64.b64decode(node.value)
    return list(struct.unpack('H' * (len(data) // 2), data))


def uint32Array(_loader, node):
    data = base64.b64decode(node.value)
    return list(struct.unpack('I' * (len(data) // 4), data))


def int8Array(_loader, node):
    data = base64.b64decode(node.value)
    return list(struct.unpack('b' * (len(data) // 1), data))


def int16Array(_loader, node):
    data = base64.b64decode(node.value)
    return list(struct.unpack('h' * (len(data) // 2), data))


def int32Array(_loader, node):
    data = base64.b64decode(node.value)
    return list(struct.unpack('i' * (len(data) // 4), data))


#type:ignore
yaml.add_constructor('tag:yaml.org,2002:js/Float32Array', float32Array)
yaml.add_constructor('tag:yaml.org,2002:js/Float64Array', float64Array)
yaml.add_constructor('tag:yaml.org,2002:js/Uint8Array', uint8Array)
yaml.add_constructor('tag:yaml.org,2002:js/Uint8ClampedArray',
                     uint8ClampedArray)
yaml.add_constructor('tag:yaml.org,2002:js/Uint16Array', uint16Array)
yaml.add_constructor('tag:yaml.org,2002:js/Uint32Array', uint32Array)
yaml.add_constructor('tag:yaml.org,2002:js/Int8Array', int8Array)
yaml.add_constructor('tag:yaml.org,2002:js/Int16Array', int16Array)
yaml.add_constructor('tag:yaml.org,2002:js/Int32Array', int32Array)


class IO(object):
    """
    IO 模块，抽象 bytes/file <-> object 的 load/dump 操作，支持 gzip 压缩和 yaml、ubjson 序列化 读取时依据 magic number 自动识别压缩格式，写入时默认使用 gzip
    """

    @staticmethod
    def serialize(obj, format, compress='gzip') -> bytes:
        """
        根据format序列化模型
        format 支持 json, ubjson, yaml, zstd
        compress 支持 gzip
        """
        result = None
        if format == 'json':
            result = json.dumps(obj).encode(encoding="utf-8")
        if format == 'ubjson':
            result = ubjson.dumpb(obj)
        if format == 'yaml':
            result = yaml.dump(obj).encode(encoding="utf-8")

        if result is None:
            assert False, 'format not support'
        if compress == 'gzip':
            return gzip.compress(result)
        if compress == 'zstd':
            return zstd.ZstdCompressor().compress(result)
        return result

    @staticmethod
    def deserialize(byt, format):
        """
        根据format反序列化模型
        format 支持 json, ubjson, yaml, zstd
        """
        if format == 'json':
            return json.loads(byt)
        if format == 'ubjson':
            return ubjson.loadb(byt)
        if format == 'yaml':
            return yaml.load(io.BytesIO(byt), Loader=yaml.FullLoader)
        assert False, 'format not support'

    @staticmethod
    def load(file, format):
        """
        根据format从文件中加载模型
        format 支持 json, ubjson, yaml
        """
        ### 读取文件
        f = open(file, 'r+', encoding='utf-8')
        t = f.buffer.read(4)
        f.close()
        ### 判断文件格式是否是gzip或其他格式
        if t[0:2] == b'\x1f\x8b':
            with gzip.open(file, 'rb') as input_file:
                return IO.deserialize(input_file.read(), format)  # type:ignore
        if t == b'\x28\xb5\x2f\xfd':
            with open(file, 'rb') as input_file:
                return IO.deserialize(
                    zstd.ZstdDecompressor().decompress(input_file.read()),
                    format)
        else:
            with open(file, 'rb') as f:
                data = f.read()
                f.close()
            return IO.deserialize(data, format)

    @staticmethod
    def dump(obj, file, format, compress='gzip'):
        """
        根据format将模型保存到文件中
        format 支持 json, ubjson, yaml, zstd
        compress 支持 gzip
        """
        ### 序列化
        data = IO.serialize(obj, format, compress)
        ### 写入文件
        with open(file, 'wb') as f:
            f.write(data)
            f.close()


if __name__ == '__main__':
    obj = [
        123, 1.25, 43121609.5543, 12345.44e40, 'a', 'here is a string', None,
        True, False, [[1, 2], 3, [4, 5, 6], 7], {
            'a dict': 456
        }
    ]
    IO.dump(obj, 'output.json.gz', 'json')
    IO.dump(obj, 'output.ubjson.gz', 'ubjson')
    IO.dump(obj, 'output.yaml.gz', 'yaml')  # type: ignore
    IO.dump(obj, 'output.yaml.zstd', 'yaml', 'zstd')  # type: ignore
    print(IO.load('output.json.gz', 'json'))
    print(IO.load('output.ubjson.gz', 'ubjson'))
    print(IO.load('output.yaml.gz', 'yaml'))
    print(IO.load('output.yaml.zstd', 'yaml'))
