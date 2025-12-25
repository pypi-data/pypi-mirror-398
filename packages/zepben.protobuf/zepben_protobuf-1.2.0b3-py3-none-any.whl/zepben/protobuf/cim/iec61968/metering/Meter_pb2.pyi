from zepben.protobuf.cim.iec61968.metering import EndDevice_pb2 as _EndDevice_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Meter(_message.Message):
    __slots__ = ("ed",)
    ED_FIELD_NUMBER: _ClassVar[int]
    ed: _EndDevice_pb2.EndDevice
    def __init__(self, ed: _Optional[_Union[_EndDevice_pb2.EndDevice, _Mapping]] = ...) -> None: ...
