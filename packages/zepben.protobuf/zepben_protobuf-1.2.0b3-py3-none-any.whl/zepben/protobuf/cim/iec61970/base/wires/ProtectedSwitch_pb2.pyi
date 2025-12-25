from zepben.protobuf.cim.iec61970.base.wires import Switch_pb2 as _Switch_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ProtectedSwitch(_message.Message):
    __slots__ = ("sw", "breakingCapacityNull", "breakingCapacitySet", "relayFunctionMRIDs")
    SW_FIELD_NUMBER: _ClassVar[int]
    BREAKINGCAPACITYNULL_FIELD_NUMBER: _ClassVar[int]
    BREAKINGCAPACITYSET_FIELD_NUMBER: _ClassVar[int]
    RELAYFUNCTIONMRIDS_FIELD_NUMBER: _ClassVar[int]
    sw: _Switch_pb2.Switch
    breakingCapacityNull: _struct_pb2.NullValue
    breakingCapacitySet: int
    relayFunctionMRIDs: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, sw: _Optional[_Union[_Switch_pb2.Switch, _Mapping]] = ..., breakingCapacityNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., breakingCapacitySet: _Optional[int] = ..., relayFunctionMRIDs: _Optional[_Iterable[str]] = ...) -> None: ...
