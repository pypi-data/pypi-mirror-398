import struct
from typing import Any,List

from .utils import calc_crc

from .message_protocol import CommandConf
from .packet_parser import PacketParser

ACEINNA_BINNARY_V1 = 'AceinnaBinaryV1'
ACEINNA_BINNARY_V2 = 'AceinnaBinaryV2'
ACEINNA_BINNARY_V3 = 'AceinnaBinaryV3'
ACEINNA_BINNARY_V4 = 'AceinnaBinaryV4'

PREAMBLE = [0x55,0x55]

def build_payload_length_fmt(format:str)->str:
    if format == ACEINNA_BINNARY_V1:
        return 'B'
    elif format == ACEINNA_BINNARY_V2:
        return '<I'
    elif format == ACEINNA_BINNARY_V3 or format == ACEINNA_BINNARY_V4:
        return '<H'
    else:
        raise Exception(f'Unsupported format: {format}')

class CommandBuilder:
    __device_type = ''
    __builder = {}
    __config = None
    __data_parser = None
    
    @property
    def device_type(self):
        return self.__device_type
    
    def __init__(self, data_parser: PacketParser):
        self.__config = data_parser.config
        self.__device_type = data_parser.device_type
        self.__data_parser = data_parser
    
    def __to_command(self, command_conf: CommandConf, payload: bytes)->bytes:
        '''
        Build uart packet, default AceinnaBinnary V1
        Aceinna Binary V1: preamble|packet_type|length(1-byte)|payload|crc. Used in IMU, RTK330LA, RTK350LA
        Aceinna Binary V2: preamble|packet_type|length(4-bytes)|payload|crc. Used in INS401, INS402.
        Aceinna Binary V3: preamble|packet_type(2-bytes)|length|counter(2-bytes)|payload|crc. Used in INS502 and later products
        Aceinna Binary V4: preamble|packet_type(2-bytes)|length|payload|crc. Used from INS502 31.02.00
        '''
        command_bytes = bytearray()
        # append packet type
        packet = bytearray(command_conf.request_packet)
        payload_length_fmt = build_payload_length_fmt(command_conf.format) 
        payload_len = len(payload)
        # append packet length
        packet.extend(struct.pack(payload_length_fmt, payload_len))
        
        if command_conf.format == ACEINNA_BINNARY_V3:
            # append packet counter
            packet.extend(struct.pack('<H', 0)) # counter

        # append payload
        packet.extend(payload)
        
        # calculate crc
        crc_bytes = calc_crc(packet)
        
        # preamble + packet + crc
        command_bytes.extend(PREAMBLE)
        command_bytes.extend(packet)
        command_bytes.extend(crc_bytes)
        
        return bytes(command_bytes)
    
    def __init_command_builder(self, command:str):
        exist_command = next((cmd for cmd in self.__config.commands if cmd.name==command), None)
        
        def builder(args)->bytes:
            payload_bytes = self.__data_parser.encode(command, args)            
            return self.__to_command(exist_command, payload_bytes)
            
        if exist_command != None:
            return builder
        
        return None
    
    def create(self, command:str, *args)->bytes:
        if command not in self.__builder:
            builder = self.__init_command_builder(command)
            if builder == None:
                raise Exception(f'Command {command} not found in protocol')
            self.__builder[command] = builder
        else:
            builder = self.__builder[command]

        return builder(args)
