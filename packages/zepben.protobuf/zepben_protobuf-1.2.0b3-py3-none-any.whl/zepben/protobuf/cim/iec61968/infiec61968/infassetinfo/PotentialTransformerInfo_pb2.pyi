from zepben.protobuf.cim.iec61968.assets import AssetInfo_pb2 as _AssetInfo_pb2
from zepben.protobuf.cim.iec61968.infiec61968.infcommon import Ratio_pb2 as _Ratio_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PotentialTransformerInfo(_message.Message):
    __slots__ = ("ai", "accuracyClassNull", "accuracyClassSet", "nominalRatio", "primaryRatioNull", "primaryRatioSet", "ptClassNull", "ptClassSet", "ratedVoltageNull", "ratedVoltageSet", "secondaryRatioNull", "secondaryRatioSet")
    AI_FIELD_NUMBER: _ClassVar[int]
    ACCURACYCLASSNULL_FIELD_NUMBER: _ClassVar[int]
    ACCURACYCLASSSET_FIELD_NUMBER: _ClassVar[int]
    NOMINALRATIO_FIELD_NUMBER: _ClassVar[int]
    PRIMARYRATIONULL_FIELD_NUMBER: _ClassVar[int]
    PRIMARYRATIOSET_FIELD_NUMBER: _ClassVar[int]
    PTCLASSNULL_FIELD_NUMBER: _ClassVar[int]
    PTCLASSSET_FIELD_NUMBER: _ClassVar[int]
    RATEDVOLTAGENULL_FIELD_NUMBER: _ClassVar[int]
    RATEDVOLTAGESET_FIELD_NUMBER: _ClassVar[int]
    SECONDARYRATIONULL_FIELD_NUMBER: _ClassVar[int]
    SECONDARYRATIOSET_FIELD_NUMBER: _ClassVar[int]
    ai: _AssetInfo_pb2.AssetInfo
    accuracyClassNull: _struct_pb2.NullValue
    accuracyClassSet: str
    nominalRatio: _Ratio_pb2.Ratio
    primaryRatioNull: _struct_pb2.NullValue
    primaryRatioSet: float
    ptClassNull: _struct_pb2.NullValue
    ptClassSet: str
    ratedVoltageNull: _struct_pb2.NullValue
    ratedVoltageSet: int
    secondaryRatioNull: _struct_pb2.NullValue
    secondaryRatioSet: float
    def __init__(self, ai: _Optional[_Union[_AssetInfo_pb2.AssetInfo, _Mapping]] = ..., accuracyClassNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., accuracyClassSet: _Optional[str] = ..., nominalRatio: _Optional[_Union[_Ratio_pb2.Ratio, _Mapping]] = ..., primaryRatioNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., primaryRatioSet: _Optional[float] = ..., ptClassNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., ptClassSet: _Optional[str] = ..., ratedVoltageNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., ratedVoltageSet: _Optional[int] = ..., secondaryRatioNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., secondaryRatioSet: _Optional[float] = ...) -> None: ...
