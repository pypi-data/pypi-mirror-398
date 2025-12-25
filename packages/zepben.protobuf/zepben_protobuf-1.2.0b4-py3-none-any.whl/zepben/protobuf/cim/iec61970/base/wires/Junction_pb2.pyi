from zepben.protobuf.cim.iec61970.base.wires import Connector_pb2 as _Connector_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Junction(_message.Message):
    __slots__ = ("cn",)
    CN_FIELD_NUMBER: _ClassVar[int]
    cn: _Connector_pb2.Connector
    def __init__(self, cn: _Optional[_Union[_Connector_pb2.Connector, _Mapping]] = ...) -> None: ...
