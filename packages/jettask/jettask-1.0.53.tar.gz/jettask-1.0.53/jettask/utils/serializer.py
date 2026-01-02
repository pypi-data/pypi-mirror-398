"""
MessagePack序列化工具模块
直接使用二进制，无 Base64 开销
"""
import msgpack


def dumps(obj):
    return msgpack.packb(obj, use_bin_type=True)


def loads(data):
    if isinstance(data, str):
        data = data.encode('latin-1')
    return msgpack.unpackb(data, raw=False, strict_map_key=False)


def dumps_str(obj):
    return msgpack.packb(obj, use_bin_type=True)


def loads_str(data):
    return msgpack.unpackb(data, raw=False, strict_map_key=False)


SERIALIZER = "msgpack_binary"