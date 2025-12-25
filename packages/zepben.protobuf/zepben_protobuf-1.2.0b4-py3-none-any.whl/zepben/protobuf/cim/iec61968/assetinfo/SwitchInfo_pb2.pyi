from zepben.protobuf.cim.iec61968.assets import AssetInfo_pb2 as _AssetInfo_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SwitchInfo(_message.Message):
    __slots__ = ("ai", "ratedInterruptingTimeNull", "ratedInterruptingTimeSet")
    AI_FIELD_NUMBER: _ClassVar[int]
    RATEDINTERRUPTINGTIMENULL_FIELD_NUMBER: _ClassVar[int]
    RATEDINTERRUPTINGTIMESET_FIELD_NUMBER: _ClassVar[int]
    ai: _AssetInfo_pb2.AssetInfo
    ratedInterruptingTimeNull: _struct_pb2.NullValue
    ratedInterruptingTimeSet: float
    def __init__(self, ai: _Optional[_Union[_AssetInfo_pb2.AssetInfo, _Mapping]] = ..., ratedInterruptingTimeNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., ratedInterruptingTimeSet: _Optional[float] = ...) -> None: ...
