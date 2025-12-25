from zepben.protobuf.cim.iec61968.assets import AssetInfo_pb2 as _AssetInfo_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class TransformerTankInfo(_message.Message):
    __slots__ = ("ai", "powerTransformerInfoMRID", "transformerEndInfoMRIDs")
    AI_FIELD_NUMBER: _ClassVar[int]
    POWERTRANSFORMERINFOMRID_FIELD_NUMBER: _ClassVar[int]
    TRANSFORMERENDINFOMRIDS_FIELD_NUMBER: _ClassVar[int]
    ai: _AssetInfo_pb2.AssetInfo
    powerTransformerInfoMRID: str
    transformerEndInfoMRIDs: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, ai: _Optional[_Union[_AssetInfo_pb2.AssetInfo, _Mapping]] = ..., powerTransformerInfoMRID: _Optional[str] = ..., transformerEndInfoMRIDs: _Optional[_Iterable[str]] = ...) -> None: ...
