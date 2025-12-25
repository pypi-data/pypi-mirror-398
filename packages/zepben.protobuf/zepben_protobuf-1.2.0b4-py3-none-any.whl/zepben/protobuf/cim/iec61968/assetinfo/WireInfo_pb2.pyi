from zepben.protobuf.cim.iec61968.assetinfo import WireMaterialKind_pb2 as _WireMaterialKind_pb2
from zepben.protobuf.cim.iec61968.assetinfo import WireInsulationKind_pb2 as _WireInsulationKind_pb2
from zepben.protobuf.cim.iec61968.assets import AssetInfo_pb2 as _AssetInfo_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class WireInfo(_message.Message):
    __slots__ = ("ai", "ratedCurrentNull", "ratedCurrentSet", "material", "sizeDescriptionNull", "sizeDescriptionSet", "strandCountNull", "strandCountSet", "coreStrandCountNull", "coreStrandCountSet", "insulatedNull", "insulatedSet", "insulationMaterial", "insulationThicknessNull", "insulationThicknessSet")
    AI_FIELD_NUMBER: _ClassVar[int]
    RATEDCURRENTNULL_FIELD_NUMBER: _ClassVar[int]
    RATEDCURRENTSET_FIELD_NUMBER: _ClassVar[int]
    MATERIAL_FIELD_NUMBER: _ClassVar[int]
    SIZEDESCRIPTIONNULL_FIELD_NUMBER: _ClassVar[int]
    SIZEDESCRIPTIONSET_FIELD_NUMBER: _ClassVar[int]
    STRANDCOUNTNULL_FIELD_NUMBER: _ClassVar[int]
    STRANDCOUNTSET_FIELD_NUMBER: _ClassVar[int]
    CORESTRANDCOUNTNULL_FIELD_NUMBER: _ClassVar[int]
    CORESTRANDCOUNTSET_FIELD_NUMBER: _ClassVar[int]
    INSULATEDNULL_FIELD_NUMBER: _ClassVar[int]
    INSULATEDSET_FIELD_NUMBER: _ClassVar[int]
    INSULATIONMATERIAL_FIELD_NUMBER: _ClassVar[int]
    INSULATIONTHICKNESSNULL_FIELD_NUMBER: _ClassVar[int]
    INSULATIONTHICKNESSSET_FIELD_NUMBER: _ClassVar[int]
    ai: _AssetInfo_pb2.AssetInfo
    ratedCurrentNull: _struct_pb2.NullValue
    ratedCurrentSet: int
    material: _WireMaterialKind_pb2.WireMaterialKind
    sizeDescriptionNull: _struct_pb2.NullValue
    sizeDescriptionSet: str
    strandCountNull: _struct_pb2.NullValue
    strandCountSet: str
    coreStrandCountNull: _struct_pb2.NullValue
    coreStrandCountSet: str
    insulatedNull: _struct_pb2.NullValue
    insulatedSet: bool
    insulationMaterial: _WireInsulationKind_pb2.WireInsulationKind
    insulationThicknessNull: _struct_pb2.NullValue
    insulationThicknessSet: float
    def __init__(self, ai: _Optional[_Union[_AssetInfo_pb2.AssetInfo, _Mapping]] = ..., ratedCurrentNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., ratedCurrentSet: _Optional[int] = ..., material: _Optional[_Union[_WireMaterialKind_pb2.WireMaterialKind, str]] = ..., sizeDescriptionNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., sizeDescriptionSet: _Optional[str] = ..., strandCountNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., strandCountSet: _Optional[str] = ..., coreStrandCountNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., coreStrandCountSet: _Optional[str] = ..., insulatedNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., insulatedSet: bool = ..., insulationMaterial: _Optional[_Union[_WireInsulationKind_pb2.WireInsulationKind, str]] = ..., insulationThicknessNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., insulationThicknessSet: _Optional[float] = ...) -> None: ...
