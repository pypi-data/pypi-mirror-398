__all__ = ['create_parser', 'create_command_builder']

from .command_builder import CommandBuilder
from .packet_parser import PacketParser
from .message_protocol import (create_internel_protocol,create_protocol_from_path,MessageProtocol)

def create_protocol(device_type:str, config_path=None)->MessageProtocol:
    if config_path == None:
        protocol = create_internel_protocol(device_type)
    else:
        protocol = create_protocol_from_path(config_path)
    
    return protocol

def create_parser(device_type:str, config_path=None)->PacketParser:
    protocol = create_protocol(device_type, config_path)
    
    return PacketParser(device_type, protocol)

def create_command_builder(device_type:str, config_path=None)->CommandBuilder:
    parser = create_parser(device_type, config_path)
    
    return CommandBuilder(parser)
