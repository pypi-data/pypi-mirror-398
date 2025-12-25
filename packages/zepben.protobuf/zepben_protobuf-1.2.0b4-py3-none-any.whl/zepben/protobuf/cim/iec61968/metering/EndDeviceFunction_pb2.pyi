from zepben.protobuf.cim.iec61968.assets import AssetFunction_pb2 as _AssetFunction_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class EndDeviceFunction(_message.Message):
    __slots__ = ("af", "enabledNull", "enabledSet")
    AF_FIELD_NUMBER: _ClassVar[int]
    ENABLEDNULL_FIELD_NUMBER: _ClassVar[int]
    ENABLEDSET_FIELD_NUMBER: _ClassVar[int]
    af: _AssetFunction_pb2.AssetFunction
    enabledNull: _struct_pb2.NullValue
    enabledSet: bool
    def __init__(self, af: _Optional[_Union[_AssetFunction_pb2.AssetFunction, _Mapping]] = ..., enabledNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., enabledSet: bool = ...) -> None: ...
