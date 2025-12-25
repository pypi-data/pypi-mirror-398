import random
import struct
import decimal
from typing import List, Any,Union
from .message_protocol import ParameterConf

BASIC_DATA_TYPES = [
    'int8','uint8','int16','uint16','int32','uint32','int64','uint64','float','double'
]

EXTEND_DATA_TYPES = [
    'string', 
    'uint8_array',
    'output_array', # List of packet_type(uint16), odr(uint8)
    'output_update_array',
    'output_update_result_array'
]

SPECIAL_DATA_TYPES = ['bits']

PARAMETERS_DATA_TYPES = ['parameter_array','update_result_array']

PARAMETER_DATA_TYPES = ['orientation','IPV4','IPV6','mac_address']

MANUFACTORY_DATA_TYPES = ['manufactory_array', 'update_manufactory_result_array']
    
ORIENTATION_MAPPING = {
  '+Ux+Uy+Uz': 0x0000,
  '-Ux-Uy+Uz': 0x0009,
  '-Uy+Ux+Uz': 0x0023,
  '+Uy-Ux+Uz': 0x002A,
  '-Ux+Uy-Uz': 0x0041,
  '+Ux-Uy-Uz': 0x0048,
  '+Uy+Ux-Uz': 0x0062,
  '-Uy-Ux-Uz': 0x006B,
  '-Uz+Uy+Ux': 0x0085,
  '+Uz-Uy+Ux': 0x008C,
  '+Uy+Uz+Ux': 0x0092,
  '-Uy-Uz+Ux': 0x009B,
  '+Uz+Uy-Ux': 0x00C4,
  '-Uz-Uy-Ux': 0x00CD,
  '-Uy+Uz-Ux': 0x00D3,
  '+Uy-Uz-Ux': 0x00DA,
  '-Ux+Uz+Uy': 0x0111,
  '+Ux-Uz+Uy': 0x0118,
  '+Uz+Ux+Uy': 0x0124,
  '-Uz-Ux+Uy': 0x012D,
  '+Ux+Uz-Uy': 0x0150,
  '-Ux-Uz-Uy': 0x0159,
  '-Uz+Ux-Uy': 0x0165,
  '+Uz-Ux-Uy': 0x016C,
}

def build_fmt(fmt:str, endian:str)->str:
    if endian == 'lsb':
        return '<'+fmt
    else:
        return '>'+fmt

def decode_field(data_type:str, endian:str, payload:bytes, start:int, precision:int=0)->Union[int,float,str,bytes]:
    result = None
    if data_type == 'uint64':
        result = (struct.unpack(build_fmt('Q',endian), payload[start:start+8])[0],8)
    elif data_type == 'int64':
        result = (struct.unpack(build_fmt('q',endian), payload[start:start+8])[0],8)
    elif data_type == 'double':
        result = (struct.unpack(build_fmt('d',endian), payload[start:start+8])[0],8)
    elif data_type == 'uint32':
        result = (struct.unpack(build_fmt('I',endian), payload[start:start+4])[0],4)
    elif data_type == 'int32':
        result = (struct.unpack(build_fmt('i',endian), payload[start:start+4])[0],4)
    elif data_type == 'float':
        # use decimal, float type is a special case
        unpack_value = struct.unpack(build_fmt('f',endian), payload[start:start+4])[0]
        if precision > 0 :
            decimal_wrapped = decimal.Decimal(unpack_value)
            try:
                unpack_value = float(round(decimal_wrapped, precision))
            except:
                unpack_value = 0
        result = (unpack_value, 4)
    elif data_type == 'uint16':
        result = (struct.unpack(build_fmt('H',endian), payload[start:start+2])[0],2)
    elif data_type == 'int16':
        result = (struct.unpack(build_fmt('h',endian), payload[start:start+2])[0],2)
    elif data_type == 'uint8':
        result = (struct.unpack('B', payload[start:start+1])[0],1)
    elif data_type == 'int8':
        result = (struct.unpack('b', payload[start:start+1])[0],1)
    else:
        raise ValueError('Decode failed, unknown data type: {0}'.format(data_type))

    return result

def encode_field(data_type:str, endian:str, value:int)->bytes:
    payload = bytearray()

    if data_type == 'uint64':
        payload = struct.pack(build_fmt('Q',endian), value)
    elif data_type == 'int64':
        payload = struct.pack(build_fmt('q',endian), value)
    elif data_type == 'double':
        payload = struct.pack(build_fmt('d',endian), value)
    elif data_type == 'uint32':
        payload = struct.pack(build_fmt('I',endian), value)
    elif data_type == 'int32':
        payload = struct.pack(build_fmt('i',endian), value)
    elif data_type == 'float':
        payload = struct.pack(build_fmt('f',endian), value)
    elif data_type == 'uint16':
        payload = struct.pack(build_fmt('H',endian), value)
    elif data_type == 'int16':
        payload = struct.pack(build_fmt('h',endian), value)
    elif data_type == 'uint8':
        payload = struct.pack(build_fmt('B',endian), value)
    elif data_type == 'int8':
        payload = struct.pack(build_fmt('b',endian), value)
    else:
        raise ValueError('Encode failed, unknown data type: {0}'.format(data_type))
    return payload

def decode_extend_field(data_type:str, payload:bytes, start:int):
    '''Cover string, uint8_array, output_array, output_update_array, orientation
    '''
    result = None

    field_payload = payload[start:]
    if data_type == 'string':
        result = (field_payload.decode('utf-8', errors='ignore'), len(field_payload))
    elif data_type == 'uint8_array':
        result = (list(field_payload), len(field_payload))
    elif data_type == 'output_array':
        result = __decode_output_array(field_payload)
    elif data_type == 'output_update_array':
        result = __decode_output_update_array(field_payload)
    elif data_type == 'output_update_result_array':
        result = __decode_output_update_result_array(field_payload)
    else:
        raise ValueError('Decode failed, unknown extend data type: {0}'.format(data_type))
    
    return result

def encode_extend_field(data_type:str, value:Any)->bytes:
    '''Cover string, uint8_array, output_array, output_update_array, orientation
    '''
    payload = bytearray()
    
    if data_type == 'string':
        payload = value.encode('utf-8')
    elif data_type == 'uint8_array':
        payload = bytes(value)
    elif data_type == 'output_array':
        payload = __encode_output_array(value)
    elif data_type == 'output_update_array':
        payload = __encode_output_update_array(value)
    elif data_type == 'output_update_result_array':
        payload = __encode_output_update_result_array(value)
    else:
        raise ValueError('Encode failed, unknown extend data type: {0}'.format(data_type))
    
    return payload

def decode_parameters_field(data_type:str, parameters: List[ParameterConf], payload:bytes, start:int)->bytes:
    '''parameter_array, update_result_array
    '''
    result = None
    if data_type == 'parameter_array':
        result = __decode_parameter_array(parameters, payload[start:])
    elif data_type == 'update_result_array':
        result =__decode_update_result(parameters, payload[start:])
    else:
        raise ValueError('Decode failed, unknown parameters data type: {0}'.format(data_type))
    
    return result

def encode_parameters_field(data_type:str, parameters: List[ParameterConf], value:int)->bytes:
    '''parameter_array, update_result_array
    '''
    payload = bytearray()
    
    if data_type == 'parameter_array':
        payload = __encode_parameter_array(parameters, value)
    elif data_type == 'update_result_array':
        payload = __encode_update_result(parameters, value)
    else:
        raise ValueError('Encode failed, unknown parameters data type: {0}'.format(data_type))
    
    return payload

def decode_manfuactory_field(data_type:str, parameters: List[ParameterConf], payload:bytes, start:int)->bytes:
    '''manufactory_array, update_manufactory_result_array
    '''
    result = None
    if data_type == 'manufactory_array':
        result = __decode_manufactory_array(parameters, payload[start:])
    elif data_type == 'update_manufactory_result_array':
        result = __decode_update_manufactory_result_array(parameters, payload[start:])
    else:
        raise ValueError('Decode failed, unknown manufactory data type: {0}'.format(data_type))
    
    return result

def encode_manfuactory_field(data_type:str, parameters: List[ParameterConf], value:Any)->bytes:
    '''manufactory_array
    '''
    payload = bytearray()
    if data_type == 'manufactory_array':
        payload = __encode_manufactory_array(parameters, value)
    elif data_type == 'update_manufactory_result_array':
        payload = __encode_update_manufactory_result_array(parameters, value)
    else:
        raise ValueError('Encode failed, unknown manufactory data type: {0}'.format(data_type))
    
    return payload

def decode_bits_field(payload:bytes, start_bit:int, length:int, endian:str = 'lsb')->int:
    """
    Decode a value from specific bits in the payload.
    """
    # Convert the entire payload to a large integer
    # 'lsb' (Little Endian) usually means the 0th byte is the least significant.
    byte_order = 'little' if endian == 'lsb' else 'big'
    payload_int = int.from_bytes(payload, byte_order)
    
    # Extract the bits
    # Shift right to move the target bits to LSB, then mask
    value = (payload_int >> start_bit) & ((1 << length) - 1)
    return value

def encode_bits_field(current_payload_int: int, value: int, start_bit: int, length: int) -> int:
    """
    Encode a value into specific bits in the payload integer.
    """
    mask = (1 << length) - 1
    value = int(value) & mask # Ensure value fits in length
    current_payload_int |= (value << start_bit)
    return current_payload_int

def __decode_output_array(payload:bytes):
    '''List of packet_type(uint16), odr(uint8)
    '''
    result = []
    for i in range(0, len(payload), 3):
        packet_type = decode_field('uint16', 'lsb', payload, i)[0]
        odr = decode_field('uint8', 'lsb', payload, i+2)[0]

        result.append({'packet_type':packet_type, 'odr':odr})
    
    return result,len(payload)

def __encode_output_array(value:dict):
    payload = bytearray()
    for item in value:
        packet_type = encode_field('uint16', 'lsb', item['packet_type'])
        odr = encode_field('uint8', 'lsb', item['odr'])
        payload.extend(packet_type)
        payload.extend(odr)
        
    return payload

def __decode_output_update_array(payload:bytes):
    '''List of packet_type(uint16), interface_type(uint8), odr(uint8)
    '''
    result = []
    
    for i in range(0, len(payload), 4):
        packet_type = decode_field('uint16', 'lsb', payload, i)[0]
        interface = decode_field('uint8', 'lsb', payload, i+2)[0]
        odr = decode_field('uint8', 'lsb', payload, i+3)[0]

        result.append({'packet_type':packet_type, 'interface_type':interface, 'odr':odr})
    
    return result,len(payload)

def __encode_output_update_array(value:dict):
    payload = bytearray()
    
    for item in value:
        packet_type = encode_field('uint16', 'lsb', item['packet_type'])
        interface = encode_field('uint8', 'lsb', item['interface_type'])
        odr = encode_field('uint8', 'lsb', item['odr'])
        
        payload.extend(packet_type)
        payload.extend(interface)
        payload.extend(odr)
    
    return payload

def __decode_output_update_result_array(payload:bytes):
    '''List of packet_type(uint16), interface_type(uint8), result(uint8)
    '''
    result = []
    
    for i in range(0, len(payload), 4):
        packet_type = decode_field('uint16', 'lsb', payload, i)[0]
        interface = decode_field('uint8', 'lsb', payload, i+2)[0]
        update_result = decode_field('uint8', 'lsb', payload, i+3)[0]

        result.append({'packet_type':packet_type, 'interface_type':interface, 'result':update_result})
    
    return result,len(payload)

def __encode_output_update_result_array(value:dict):
    payload = bytearray()
    
    for item in value:
        packet_type = encode_field('uint16', 'lsb', item['packet_type'])
        interface = encode_field('uint8', 'lsb', item['interface_type'])
        result = encode_field('uint8', 'lsb', item['result'])
        
        payload.extend(packet_type)
        payload.extend(interface)
        payload.extend(result)
    
    return payload

def __decode_parameter_array(parameters: List[ParameterConf], payload:bytes):
    '''parameter_array = List of parameter_id(uint8), parameter_len(uint8), parameter_value(length is parameter_len)
    '''
    result = []
    start = 0
    while start < len(payload):
        param_id = payload[start]
        param_len = payload[start+1]
        param_value_start = start+2

        param_conf = next((p for p in parameters if p.param_id == param_id), None)
        # TODO: handle param_conf is None

        value, data_len = __decode_parameter_field(param_conf, payload[param_value_start:param_value_start+param_len])
        result.append({
            'param_id':param_id,
            'name': param_conf.name,
            'value':value
        })
        start = start + param_value_start + data_len
    
    return result, len(payload)

def __encode_parameter_array(parameters: List[ParameterConf], value:List[Any])->bytes:
    '''parameter_array
    '''
    payload = bytearray()

    for item in value:
        param_conf = next((p for p in parameters if p.param_id == item['param_id']), None)
        # TODO: handle param_conf is None

        param_id = encode_field('uint8', 'lsb', item['param_id'])
        param_value = __encode_parameter_field(param_conf, item['value'])
        param_len = encode_field('uint8', 'lsb', len(param_value)) 

        payload.extend(param_id)
        payload.extend(param_len)
        payload.extend(param_value)
    
    return payload

def __decode_update_result(parameters: List[ParameterConf], payload:bytes):
    '''update_result_array = List of parameter_id(uint8), update_result(int8)
    '''
    result = []
    start = 0

    while start < len(payload):
        param_id = payload[start]
        update_result = decode_field('uint8','lsb', payload,start+1)[0]
        result.append({
            'param_id':param_id,
            'result':update_result
        })
        start = start + 2
    
    return result,len(payload)

def __encode_update_result(parameters: List[ParameterConf], value:List[Any])->bytes:
    '''update_result_array = List of parameter_id(uint8), update_result(uint8)
    '''
    payload = bytearray()
    for item in value:
        param_id = encode_field('uint8', 'lsb', item['param_id'])
        update_result = encode_field('uint8', 'lsb', item['result'])
        
        payload.extend(param_id)
        payload.extend(update_result)
    
    return payload

def __decode_manufactory_array(parameters: List[ParameterConf], payload:bytes):
    '''manufactory_array = List of content_id(uint8), content_len(uint8), content_value(length is content_len)
    '''
    result = []
    start = 0
    while start < len(payload):
        param_id = payload[start]
        param_len = payload[start+1]
        param_value_start = start+2

        param_conf = next((p for p in parameters if p.param_id == param_id), None)
        # TODO: handle param_conf is None

        value, data_len = __decode_parameter_field(param_conf, payload[param_value_start:param_value_start+param_len])
        result.append({
            'content_id':param_id,
            'name': param_conf.name,
            'value':value
        })
        start = param_value_start + data_len
    
    return result, len(payload)

def __encode_manufactory_array(parameters: List[ParameterConf], value:List[Any])->bytes:
    '''manufactory_array
    '''
    payload = bytearray()

    for item in value:
        param_conf = next((p for p in parameters if p.param_id == item['content_id']), None)
        # TODO: handle param_conf is None

        param_id = encode_field('uint8', 'lsb', item['content_id'])
        param_value = __encode_parameter_field(param_conf, item['value'])
        param_len = encode_field('uint8', 'lsb', len(param_value)) 

        payload.extend(param_id)
        payload.extend(param_len)
        payload.extend(param_value)
    
    return payload

def __decode_update_manufactory_result_array(parameters: List[ParameterConf], payload:bytes):
    '''update_manufactory_result_array = List of content_id(uint8), update_result(int8)
    '''
    result = []
    start = 0

    while start < len(payload):
        param_id = payload[start]
        update_result = decode_field('uint8','lsb', payload,start+1)[0]
        result.append({
            'content_id':param_id,
            'result':update_result
        })
        start = start + 2
    
    return result,len(payload)

def __encode_update_manufactory_result_array(parameters: List[ParameterConf], value:List[Any])->bytes:
    '''update_manufactory_result_array = List of content_id(uint8), update_result(uint8)
    '''
    payload = bytearray()
    for item in value:
        param_id = encode_field('uint8', 'lsb', item['content_id'])
        update_result = encode_field('uint8', 'lsb', item['result'])
        
        payload.extend(param_id)
        payload.extend(update_result)
    
    return payload

def __decode_parameter_field(param_conf: ParameterConf, payload:bytes):
    '''payattention to IPv4, IPv6, mac_address
    '''
    data_type = param_conf.type
    if data_type in BASIC_DATA_TYPES:
        return decode_field(data_type, param_conf.endian, payload, 0, param_conf.precision)
    elif data_type == 'string':
        return (payload.decode('utf-8', errors='ignore'), len(payload))
    elif data_type == 'orientation':
        return __decode_orientation(payload)
    else:
        raise ValueError('Decode failed, unknown parameter field data type: {0}'.format(data_type))

def __encode_parameter_field(param_conf: ParameterConf, value:Any)->bytes:
    '''payattention to IPv4, IPv6, mac_address
    '''
    data_type = param_conf.type
    if data_type in BASIC_DATA_TYPES:
        return encode_field(data_type, param_conf.endian, value)
    elif data_type == 'string':
        return value.encode('utf-8')
    elif data_type == 'orientation':
        return __encode_orientation(value)
    else:
        raise ValueError('Encode failed, unknown parameter field data type: {0}'.format(data_type))

def __decode_orientation(payload:bytes):
    '''orienation(uint16), convert to a string value
    '''
    value = decode_field('uint16', 'lsb', payload, 0)[0]
    #find value in ORIENTATION_MAPPING, and get the key
    for key in ORIENTATION_MAPPING:
        if ORIENTATION_MAPPING[key] == value:
            return key,2
    
    return '+Ux+Uy+Uz',2

def __encode_orientation(value:str):
    '''From a string value to orientation(uint16)
    '''
    if value in ORIENTATION_MAPPING:
        return encode_field('uint16', 'lsb', ORIENTATION_MAPPING[value])

    return bytes([0x00, 0x00])

def build_random_bits(length:int)->Union[int]:
    random_value = 0
    for i in range(length):
        bit_value = random.randint(0,1)
        random_value = random_value | (bit_value << i)
    return random_value

def build_random_value(data_type:str)->Union[int,float]:
    if data_type == 'uint64':
        return random.randint(0,18446744073709551615)
    elif data_type == 'int64':
        return random.randint(-9223372036854775808,9223372036854775807)
    elif data_type == 'uint32':
        return random.randint(0,4294967295)
    elif data_type == 'int32':
        return random.randint(-2147483648,2147483647)
    elif data_type == 'uint16':
        return random.randint(0,65535)
    elif data_type == 'int16':
        return random.randint(-32768,32767)
    elif data_type == 'uint8':
        return random.randint(0,255)
    elif data_type == 'int8':
        return random.randint(-128,127)
    elif data_type == 'double':
        return random.random()
    elif data_type == 'float':
        return random.random()
    elif data_type == 'uint8_array':
        return bytes([random.randint(0,255) for i in range(0,20)])
    else:
        raise ValueError('Build random value failed, unknown data type: {0}'.format(data_type))
