from zepben.protobuf.cim.iec61970.base.core import Equipment_pb2 as _Equipment_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PowerElectronicsUnit(_message.Message):
    __slots__ = ("eq", "maxPNull", "maxPSet", "minPNull", "minPSet", "powerElectronicsConnectionMRID")
    EQ_FIELD_NUMBER: _ClassVar[int]
    MAXPNULL_FIELD_NUMBER: _ClassVar[int]
    MAXPSET_FIELD_NUMBER: _ClassVar[int]
    MINPNULL_FIELD_NUMBER: _ClassVar[int]
    MINPSET_FIELD_NUMBER: _ClassVar[int]
    POWERELECTRONICSCONNECTIONMRID_FIELD_NUMBER: _ClassVar[int]
    eq: _Equipment_pb2.Equipment
    maxPNull: _struct_pb2.NullValue
    maxPSet: int
    minPNull: _struct_pb2.NullValue
    minPSet: int
    powerElectronicsConnectionMRID: str
    def __init__(self, eq: _Optional[_Union[_Equipment_pb2.Equipment, _Mapping]] = ..., maxPNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., maxPSet: _Optional[int] = ..., minPNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., minPSet: _Optional[int] = ..., powerElectronicsConnectionMRID: _Optional[str] = ...) -> None: ...
