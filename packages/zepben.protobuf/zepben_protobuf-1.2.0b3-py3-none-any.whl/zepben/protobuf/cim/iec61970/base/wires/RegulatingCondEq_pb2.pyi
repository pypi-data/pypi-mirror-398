from zepben.protobuf.cim.iec61970.base.wires import EnergyConnection_pb2 as _EnergyConnection_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RegulatingCondEq(_message.Message):
    __slots__ = ("ec", "controlEnabledNull", "controlEnabledSet", "regulatingControlMRID")
    EC_FIELD_NUMBER: _ClassVar[int]
    CONTROLENABLEDNULL_FIELD_NUMBER: _ClassVar[int]
    CONTROLENABLEDSET_FIELD_NUMBER: _ClassVar[int]
    REGULATINGCONTROLMRID_FIELD_NUMBER: _ClassVar[int]
    ec: _EnergyConnection_pb2.EnergyConnection
    controlEnabledNull: _struct_pb2.NullValue
    controlEnabledSet: bool
    regulatingControlMRID: str
    def __init__(self, ec: _Optional[_Union[_EnergyConnection_pb2.EnergyConnection, _Mapping]] = ..., controlEnabledNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., controlEnabledSet: bool = ..., regulatingControlMRID: _Optional[str] = ...) -> None: ...
