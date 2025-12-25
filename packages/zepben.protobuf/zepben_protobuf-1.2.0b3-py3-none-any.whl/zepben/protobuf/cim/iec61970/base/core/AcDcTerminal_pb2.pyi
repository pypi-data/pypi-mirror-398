from zepben.protobuf.cim.iec61970.base.core import IdentifiedObject_pb2 as _IdentifiedObject_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AcDcTerminal(_message.Message):
    __slots__ = ("io", "connectedNull", "connectedSet")
    IO_FIELD_NUMBER: _ClassVar[int]
    CONNECTEDNULL_FIELD_NUMBER: _ClassVar[int]
    CONNECTEDSET_FIELD_NUMBER: _ClassVar[int]
    io: _IdentifiedObject_pb2.IdentifiedObject
    connectedNull: _struct_pb2.NullValue
    connectedSet: bool
    def __init__(self, io: _Optional[_Union[_IdentifiedObject_pb2.IdentifiedObject, _Mapping]] = ..., connectedNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., connectedSet: bool = ...) -> None: ...
