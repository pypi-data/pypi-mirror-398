from typing import List,Union,Dict
from .message_protocol import (MessageProtocol,OutputConf,CommandConf,ScalingConf)
from .field_parser import(BASIC_DATA_TYPES, EXTEND_DATA_TYPES, PARAMETERS_DATA_TYPES, MANUFACTORY_DATA_TYPES, 
                          encode_field, decode_field, 
                          encode_extend_field, decode_extend_field, 
                          encode_parameters_field, decode_parameters_field,build_random_value,build_random_bits,
                          encode_manfuactory_field, decode_manfuactory_field,
                          encode_bits_field, decode_bits_field)

def get_data_type_size(data_type: str) -> int:
    if data_type in ['uint8', 'int8']: return 1
    if data_type in ['uint16', 'int16']: return 2
    if data_type in ['uint32', 'int32', 'float']: return 4
    if data_type in ['uint64', 'int64', 'double']: return 8
    return 0

class PacketParser:
    __device_type = ''
    __config = None
    __decoder = {}
    __encoder = {}

    def __init__(self, device_type:str, config: MessageProtocol):
        self.__device_type = device_type
        self.__config = config

    def __build_decoder(self, packet_type:str):
        exist_output = next((output for output in self.__config.outputs if output.name==packet_type), None)
        if exist_output != None:
            return self.__build_output_payload_decoder(exist_output, self.__config.scalings)

        exist_command = next((command for command in self.__config.commands if command.name==packet_type), None)
        if exist_command != None:
            return self.__build_command_payload_decoder(exist_command, self.__config.scalings)
        
        return lambda payload: payload

    def __build_output_payload_decoder(self, output: OutputConf, scalings: Dict[str, ScalingConf]):
        def decoder(payload: bytes)->dict:
            result = {}
            current_bit_pos = 0

            for field in output.fields:
                if hasattr(field.context, 'start') and field.context.get('start') is not None:
                    start_bit = field.context.get('start')
                else:
                    start_bit = current_bit_pos
                
                value = 0
                field_bit_len = 0

                if field.type == 'bits':
                    value = decode_bits_field(payload, start_bit, field.context.get('length'))
                    field_bit_len = field.context.get('length')
                elif field.type in BASIC_DATA_TYPES:
                    byte_start = start_bit // 8
                    value, data_len = decode_field(field.type, field.endian, payload, byte_start, field.precision)
                    field_bit_len = data_len * 8
                elif field.type in EXTEND_DATA_TYPES:
                    byte_start = start_bit // 8
                    value, data_len = decode_extend_field(field.type, payload, byte_start)
                    field_bit_len = data_len * 8
                else:
                    raise ValueError('Decode output failed, unknown data type {0} in output: {1}'.format(field.type, output.name))
                
                current_bit_pos = start_bit + field_bit_len
                
                if field.scaling in scalings:
                    value = value * scalings.get(field.scaling).scale + scalings.get(field.scaling).offset
                    if field.precision > 0 :
                        try:
                            value = float(round(value, field.precision))
                        except:
                            value = 0
                result[field.name] = value
                start_bit = start_bit + field_bit_len
            return result
        return decoder

    def __build_command_payload_decoder(self, command: CommandConf, scalings: Dict[str, ScalingConf]):
        if command.response_fields == None or len(command.response_fields) == 0:
            return lambda payload: True
        
        def decoder(payload: bytes)->dict:
            # analyze the response fields in command
            # fill the dict with the response fields
            # should check the data type in response fields
            result = {}
            start = 0
            for field in command.response_fields:
                if field.type in BASIC_DATA_TYPES:
                    value, data_len = decode_field(field.type, field.endian, payload, start)
                elif field.type in EXTEND_DATA_TYPES:
                    value, data_len = decode_extend_field(field.type, payload, start)
                elif field.type in PARAMETERS_DATA_TYPES:
                    value, data_len = decode_parameters_field(field.type, self.__config.parameters, payload, start)
                elif field.type in MANUFACTORY_DATA_TYPES:
                    value, data_len = decode_manfuactory_field(field.type, self.__config.manufactory, payload, start)
                else:
                    raise ValueError('Decode command failed, unknown data type {0} in command: {1}'.format(field.type, command.name))
                
                if field.scaling in scalings:
                    value = value * scalings.get(field.scaling).scale + scalings.get(field.scaling).offset

                result[field.name] = value
                start = start + data_len
            return result
        return decoder

    def __build_encoder(self, packet_type:str):
        exist_output = next((output for output in self.__config.outputs if output.name==packet_type), None)
        if exist_output != None:
            return self.__build_output_payload_encoder(exist_output, self.__config.scalings)
        
        #TODO: may need encoder for commands
        exist_command = next((command for command in self.__config.commands if command.name==packet_type), None)
        if exist_command != None:
            return self.__build_command_payload_encoder(exist_command, self.__config.scalings)
        
        return lambda payload: None

    def __build_output_payload_encoder(self, output: OutputConf, scalings: dict):
        def encoder(packet_value: List[int])->bytes:
            is_bit_mode = any(f.type == 'bits' for f in output.fields)
            
            if is_bit_mode:
                total_int = 0
                current_bit_pos = 0
                packet_value_len = len(packet_value)
                for idx, field in enumerate(output.fields):
                    value = 0
                    if idx < packet_value_len:
                        value = packet_value[idx]
                        if field.scaling in scalings:
                            value = int((value - scalings.get(field.scaling).offset) / scalings.get(field.scaling).scale)
                    
                    if hasattr(field.context, 'start') and field.context.get('start') is not None:
                        start_bit = field.context.get('start')
                    else:
                        start_bit = current_bit_pos
                    
                    if field.type == 'bits':
                        total_int = encode_bits_field(total_int, value, start_bit, field.context.get('length'))
                        current_bit_pos = start_bit + field.context.get('length')
                    elif field.type in BASIC_DATA_TYPES:
                        field_size = get_data_type_size(field.type)
                        total_int = total_int | (value << current_bit_pos)
                        current_bit_pos = current_bit_pos + field_size * 8
                    else:
                        raise ValueError('Encode output failed in bit mode, unknown data type {0} in output: {1}'.format(field.type, output.name))
                    
                return total_int.to_bytes(8, byteorder='little') # Assuming lsb
            else:
                result = bytearray()
                packet_value_len = len(packet_value)
                for idx, field in enumerate(output.fields):
                    value = 0
                    if idx < packet_value_len:
                        value = packet_value[idx]
                        if field.name in scalings:
                            value = int((value - scalings.get(field.scaling).offset) / scalings.get(field.scaling).scale)
                    
                    if field.type in BASIC_DATA_TYPES:
                        result.extend(encode_field(field.type, field.endian, value))
                    elif field.type in EXTEND_DATA_TYPES:
                        result.extend(encode_extend_field(field.type, value))
                    else:
                        raise ValueError('Encode output failed, unknown data type {0} in output: {1}'.format(field.type, output.name))
                return bytes(result)
        return encoder

    def __build_command_payload_encoder(self, command: CommandConf, scalings: dict):
        if command.request_fields == None or len(command.request_fields) == 0:
            return lambda args: bytes([])
        
        def encoder(args)->bytes:
            args_len = len(args)
            result = bytearray()
            # same as decoder, analyze the command fields
            # fill the bytes with the request fields
            for idx, field in enumerate(command.request_fields):
                value = 0
                if(idx < args_len):
                    value = args[idx]
                    if field.scaling in scalings:
                        value = int((value - scalings.get(field.scaling).offset) / scalings.get(field.scaling).scale)

                if field.type in BASIC_DATA_TYPES:
                    result.extend(encode_field(field.type, field.endian, value))
                elif field.type in EXTEND_DATA_TYPES:
                    result.extend(encode_extend_field(field.type, value))
                elif field.type in PARAMETERS_DATA_TYPES:
                    result.extend(encode_parameters_field(field.type, self.__config.parameters, value))
                elif field.type in MANUFACTORY_DATA_TYPES:
                    result.extend(encode_manfuactory_field(field.type, self.__config.manufactory, value))
                else:
                    raise ValueError('Encode command failed, unknown data type {0} in command: {1}'.format(field.type, command.name))
            return result
        return encoder

    @property
    def device_type(self):
        return self.__device_type
    
    @property
    def config(self):
        return self.__config

    def decode(self, packet_type:str, payload: bytes)->dict:
        if packet_type not in self.__decoder:
            decoder = self.__build_decoder(packet_type)
            if decoder == None:
                raise Exception('No decoder for packet type: ' + packet_type)
            self.__decoder[packet_type] = decoder
        else:
            decoder = self.__decoder[packet_type]

        return decoder(payload)

    def encode(self, packet_type:str, packet_value: dict)->bytes:
        if packet_type not in self.__encoder:
            encoder = self.__build_encoder(packet_type)
            if encoder == None:
                raise Exception('No encoder for packet type: ' + packet_type)
            self.__encoder[packet_type] = encoder
        else:
            encoder = self.__encoder[packet_type]
        
        return encoder(packet_value)
    
    def build_random_data(self, packet_type:str)->List[Union[int,float]]:
        # read payload define from the config, build a random data for the packet type
        exist_output = next((output for output in self.__config.outputs if output.name==packet_type), None)
        if exist_output == None:
            return None
        
        is_bit_mode = any(f.type == 'bits' for f in exist_output.fields)
        if is_bit_mode:
            # for bit mode, return a list with single integer value
            result = []
            for field in exist_output.fields:
                random_value = build_random_bits(field.context.get('length'))
                result.append(random_value)
            return result
        else:
            result = []
            for field in exist_output.fields:
                random_value = build_random_value(field.type)
                result.append(random_value)
            return result
