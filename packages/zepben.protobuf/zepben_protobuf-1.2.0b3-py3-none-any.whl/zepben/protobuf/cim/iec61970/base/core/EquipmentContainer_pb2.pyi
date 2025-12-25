from zepben.protobuf.cim.iec61970.base.core import ConnectivityNodeContainer_pb2 as _ConnectivityNodeContainer_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class EquipmentContainer(_message.Message):
    __slots__ = ("cnc",)
    CNC_FIELD_NUMBER: _ClassVar[int]
    cnc: _ConnectivityNodeContainer_pb2.ConnectivityNodeContainer
    def __init__(self, cnc: _Optional[_Union[_ConnectivityNodeContainer_pb2.ConnectivityNodeContainer, _Mapping]] = ...) -> None: ...
