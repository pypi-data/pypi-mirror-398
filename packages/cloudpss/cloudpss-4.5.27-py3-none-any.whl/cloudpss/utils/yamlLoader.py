import yaml
import io
import gzip
import struct
import base64



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
yaml.add_constructor('tag:yaml.org,2002:js/Float32Array',
                     float32Array)
yaml.add_constructor('tag:yaml.org,2002:js/Float64Array',
                     float64Array)
yaml.add_constructor('tag:yaml.org,2002:js/Uint8Array',
                     uint8Array)
yaml.add_constructor('tag:yaml.org,2002:js/Uint8ClampedArray',
                     uint8ClampedArray)
yaml.add_constructor('tag:yaml.org,2002:js/Uint16Array',
                     uint16Array)
yaml.add_constructor('tag:yaml.org,2002:js/Uint32Array',
                     uint32Array)
yaml.add_constructor('tag:yaml.org,2002:js/Int8Array',
                     int8Array)
yaml.add_constructor('tag:yaml.org,2002:js/Int16Array',
                     int16Array)
yaml.add_constructor('tag:yaml.org,2002:js/Int32Array',
                     int32Array)


def fileLoad(fileName):
    f = open(fileName, 'r+', encoding='utf-8')
    t = f.buffer.read(2)
    f.close()
    data = None
    if t == b'\x1f\x8b':
        with gzip.open(fileName, 'rb') as input_file:
            with io.TextIOWrapper(input_file, encoding='utf-8') as dec: # type: ignore
                r = dec.read()
                data = yaml.load(r, _loader=yaml.Full_loader) # type: ignore
    else:
        f = open(fileName, 'r+', encoding='utf-8')
        data = yaml.load(f, _loader=yaml.Full_loader) # type: ignore
        f.close()
    return data