from zepben.protobuf.cim.iec61970.base.scada import RemotePoint_pb2 as _RemotePoint_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RemoteSource(_message.Message):
    __slots__ = ("rp", "measurementMRID")
    RP_FIELD_NUMBER: _ClassVar[int]
    MEASUREMENTMRID_FIELD_NUMBER: _ClassVar[int]
    rp: _RemotePoint_pb2.RemotePoint
    measurementMRID: str
    def __init__(self, rp: _Optional[_Union[_RemotePoint_pb2.RemotePoint, _Mapping]] = ..., measurementMRID: _Optional[str] = ...) -> None: ...
