import json
import struct
from base64 import b64encode, b64decode
from typing import Optional
from typing import Tuple


def parse_get_property_message(destination_id: int, property_type: int, property_frequency: int):
    return parse_message(0x03, 0, destination_id, (property_type, 0x00, property_frequency, 0x00))


def parse_set_property_message(destination_id: int, property_type: int, property_values: Tuple):
    data = []
    for value_type, value in property_values:
        data += parse_data(value, value_type)
    return parse_message(0x04, property_type, destination_id, data)


def parse_message(command: int, source: int, destination: int,
                  byte_data: Tuple =
                  (None, None, None, None, None, None, None, None)):
    message = dict()
    message["c"] = command
    message["s"] = source
    message["d"] = destination
    message["b"] = __encode_bytes(byte_data)
    message["l"] = len(byte_data)
    return json.dumps(message, separators=(",", ":"))


def __extract_length(begin: int, src: Tuple) -> int:
    length = 1
    for i in range(begin + 1, len(src)):
        if not src[i]:
            length += 1
        else:
            break
    return length


def __encode_bytes(byte_data: Tuple):
    idx = 0
    data = bytearray(len(byte_data))
    while idx < len(byte_data):
        if not byte_data[idx]:
            idx += 1
        elif byte_data[idx] > 256:
            length = __extract_length(idx, byte_data)
            data[idx: idx + length] = int.to_bytes(
                byte_data[idx], byteorder="little", length=length, signed=True
            )
            idx += length
        elif byte_data[idx] < 0:
            data[idx: idx + 4] = int.to_bytes(
                int(byte_data[idx]), byteorder="little", length=4, signed=True
            )
            idx += 4
        elif byte_data[idx] < 256:
            data[idx] = int(byte_data[idx])
            idx += 1
    return b64encode(bytes(data)).decode("utf8")


def decode_message(message: str):
    message = json.loads(message)
    command = message["c"]
    source = message["s"]
    destination = message["d"]
    data = message["b"]
    length = message["l"]
    return command, source, destination, data, length


def unpack_data(data: str, structure: Tuple = (1, 1, 1, 1, 1, 1, 1, 1)):
    data = bytearray(b64decode(data.encode("utf8")))
    idx = 0
    result = []
    for size in structure:
        result.append(int.from_bytes(data[idx:idx + size], byteorder="little"))
        idx += size
    return result


def parse_data(values, data_type: str) -> Optional[Tuple]:
    if data_type == "string":
        return tuple(str.encode(values))
    elif data_type == "float":
        return tuple(bytearray(struct.pack("f", values)))
    elif data_type == "bytes":
        return values
    elif data_type in ["s8", "s16", "s32"]:
        return tuple(int.to_bytes(int(values), byteorder="little", signed=True, length=(int(data_type[1:])) // 8))
    elif data_type in ["u8", "u16", "u32"]:
        return tuple(int.to_bytes(int(values), byteorder="little", signed=False, length=(int(data_type[1:])) // 8))
    else:
        # error type
        return None


def decode_data(data: str) -> float:
    return round(struct.unpack("f", bytes(unpack_data(data)[:4]))[0], 2)
