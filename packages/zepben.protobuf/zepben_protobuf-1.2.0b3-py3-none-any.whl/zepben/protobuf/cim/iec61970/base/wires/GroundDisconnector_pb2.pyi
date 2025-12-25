from zepben.protobuf.cim.iec61970.base.wires import Switch_pb2 as _Switch_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GroundDisconnector(_message.Message):
    __slots__ = ("sw",)
    SW_FIELD_NUMBER: _ClassVar[int]
    sw: _Switch_pb2.Switch
    def __init__(self, sw: _Optional[_Union[_Switch_pb2.Switch, _Mapping]] = ...) -> None: ...
