# A library to decode and encode data packet for Aceinna Devices

## Usage
A simple example to decode and encode the data packet for INS502 device.
```python
from acenav_api import create_parser
    
parser = create_parser('IN502')
decode_payload = parser.decode('S2', bytes([0x0,0x1,0x2])) # return a dict object
binary_bytes = parser.encode('S2', [1,2,3]) # return as bytes
```

It also supports to pass a configuration file to the parser, the configuration file contains payload definition and the parser will generate the parser based on the configuration file.

```python
from acenav_api import create_parser

parser = create_parser('IN502-custom', 'path/to/config.json')
# support custom packet type
decode_payload = parser.decode('S2', bytes([0x0,0x1,0x2])) # return a dict object
binary_bytes = parser.encode('S2',[0,1,2]) # return as bytes
```

A examle to use the library to communicate with the device. It includes command builder, data parser.
```python
# Generate Command Builder
command_builder = create_command_builder('INS502')
# Generate Command Request Bytes
command_bytes = command_builder.create('uB', [
    {'paramId':1, 'value':1},
    {'paramId':2, 'value':2},
])

# Prepare serial_port or ethernet_port as communicator, then send request bytes
communicator.write(command_bytes)
# Read Response Bytes
read_bytes = communicator.read()
packet_bytes = fetch_last_packet(read_bytes, 'uB')

# Generate Data Parser
parser = create_parser('INS502')
# Decode Response as a dict
update_result = parser.decode('uB', packet_bytes)
```

## How it work
The libary predefined configurations for each device, the configuration file is a json file that contains the payload definition for each packet type. It will decode or encode the data based on the configuration file.

User also could pass a custom configuration file to the parser to generate the parser. It is allowed to update the payload definition in the configuration file. It could be useful if the output format is modified or the payload is changed.

## Supported Data Types
### Outputs
`uint8`, `int8`, `uint16`, `int16`, `uint32`, `int32`, `uint64`, `int64`, `float`, `double`, `string`
### Command
1. Includes data types in Outputs
2. `output_array`,`output_update_array`, `update_result_array`,`parameter_array`,`uint8_array`

## Extend Data Types
`output_array` 

Packet Odr display array. It is used in lO command response.

| Field | Type | Description |
| --- | --- | --- |
| packet_type | string | Packet Type |
| interface_type | int | Interface Type |

`output_update_array`

Packet Odr update array. It is used in sO command request.
| Field | Type | Description |
| --- | --- | --- |
| packet_type | string | Packet Type |
| interface_type | int | Interface Type |
| odr | int | Odr |

`parameter_array`

Parameter display array. It used in gB and uB command request.
| Field | Type | Description |
| --- | --- | --- |
| param_id | int | Param Id |
| value | int | Value |

`update_result_array`

Update result array. It used in uB command response.

| Field | Type | Description |
| --- | --- | --- |
| param_id | int | Param Id |
| result | int | Result |
