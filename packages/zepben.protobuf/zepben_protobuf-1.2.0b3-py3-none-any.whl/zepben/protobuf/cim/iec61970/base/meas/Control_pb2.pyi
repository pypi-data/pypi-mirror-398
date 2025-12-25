from zepben.protobuf.cim.iec61970.base.meas import IoPoint_pb2 as _IoPoint_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Control(_message.Message):
    __slots__ = ("ip", "powerSystemResourceMRID", "remoteControlMRID")
    IP_FIELD_NUMBER: _ClassVar[int]
    POWERSYSTEMRESOURCEMRID_FIELD_NUMBER: _ClassVar[int]
    REMOTECONTROLMRID_FIELD_NUMBER: _ClassVar[int]
    ip: _IoPoint_pb2.IoPoint
    powerSystemResourceMRID: str
    remoteControlMRID: str
    def __init__(self, ip: _Optional[_Union[_IoPoint_pb2.IoPoint, _Mapping]] = ..., powerSystemResourceMRID: _Optional[str] = ..., remoteControlMRID: _Optional[str] = ...) -> None: ...
