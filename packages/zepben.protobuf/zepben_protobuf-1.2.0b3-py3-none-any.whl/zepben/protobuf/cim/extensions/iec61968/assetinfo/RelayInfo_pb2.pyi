from zepben.protobuf.cim.iec61968.assets import AssetInfo_pb2 as _AssetInfo_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RelayInfo(_message.Message):
    __slots__ = ("ai", "curveSettingNull", "curveSettingSet", "recloseDelays", "recloseFastNull", "recloseFastSet")
    AI_FIELD_NUMBER: _ClassVar[int]
    CURVESETTINGNULL_FIELD_NUMBER: _ClassVar[int]
    CURVESETTINGSET_FIELD_NUMBER: _ClassVar[int]
    RECLOSEDELAYS_FIELD_NUMBER: _ClassVar[int]
    RECLOSEFASTNULL_FIELD_NUMBER: _ClassVar[int]
    RECLOSEFASTSET_FIELD_NUMBER: _ClassVar[int]
    ai: _AssetInfo_pb2.AssetInfo
    curveSettingNull: _struct_pb2.NullValue
    curveSettingSet: str
    recloseDelays: _containers.RepeatedScalarFieldContainer[float]
    recloseFastNull: _struct_pb2.NullValue
    recloseFastSet: bool
    def __init__(self, ai: _Optional[_Union[_AssetInfo_pb2.AssetInfo, _Mapping]] = ..., curveSettingNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., curveSettingSet: _Optional[str] = ..., recloseDelays: _Optional[_Iterable[float]] = ..., recloseFastNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., recloseFastSet: bool = ...) -> None: ...
