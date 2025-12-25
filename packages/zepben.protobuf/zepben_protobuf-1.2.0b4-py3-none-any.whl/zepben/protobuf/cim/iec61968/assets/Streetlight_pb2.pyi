from zepben.protobuf.cim.iec61968.assets import Asset_pb2 as _Asset_pb2
from zepben.protobuf.cim.iec61968.infiec61968.infassets import StreetlightLampKind_pb2 as _StreetlightLampKind_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Streetlight(_message.Message):
    __slots__ = ("at", "poleMRID", "lampKind", "lightRatingNull", "lightRatingSet")
    AT_FIELD_NUMBER: _ClassVar[int]
    POLEMRID_FIELD_NUMBER: _ClassVar[int]
    LAMPKIND_FIELD_NUMBER: _ClassVar[int]
    LIGHTRATINGNULL_FIELD_NUMBER: _ClassVar[int]
    LIGHTRATINGSET_FIELD_NUMBER: _ClassVar[int]
    at: _Asset_pb2.Asset
    poleMRID: str
    lampKind: _StreetlightLampKind_pb2.StreetlightLampKind
    lightRatingNull: _struct_pb2.NullValue
    lightRatingSet: int
    def __init__(self, at: _Optional[_Union[_Asset_pb2.Asset, _Mapping]] = ..., poleMRID: _Optional[str] = ..., lampKind: _Optional[_Union[_StreetlightLampKind_pb2.StreetlightLampKind, str]] = ..., lightRatingNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., lightRatingSet: _Optional[int] = ...) -> None: ...
