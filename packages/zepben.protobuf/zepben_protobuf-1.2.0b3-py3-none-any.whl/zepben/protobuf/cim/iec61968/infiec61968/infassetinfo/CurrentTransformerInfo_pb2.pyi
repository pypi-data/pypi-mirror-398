from zepben.protobuf.cim.iec61968.assets import AssetInfo_pb2 as _AssetInfo_pb2
from zepben.protobuf.cim.iec61968.infiec61968.infcommon import Ratio_pb2 as _Ratio_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CurrentTransformerInfo(_message.Message):
    __slots__ = ("ai", "accuracyClassNull", "accuracyClassSet", "accuracyLimitNull", "accuracyLimitSet", "coreCountNull", "coreCountSet", "ctClassNull", "ctClassSet", "kneePointVoltageNull", "kneePointVoltageSet", "maxRatio", "nominalRatio", "primaryRatioNull", "primaryRatioSet", "ratedCurrentNull", "ratedCurrentSet", "secondaryFlsRatingNull", "secondaryFlsRatingSet", "secondaryRatioNull", "secondaryRatioSet", "usageNull", "usageSet")
    AI_FIELD_NUMBER: _ClassVar[int]
    ACCURACYCLASSNULL_FIELD_NUMBER: _ClassVar[int]
    ACCURACYCLASSSET_FIELD_NUMBER: _ClassVar[int]
    ACCURACYLIMITNULL_FIELD_NUMBER: _ClassVar[int]
    ACCURACYLIMITSET_FIELD_NUMBER: _ClassVar[int]
    CORECOUNTNULL_FIELD_NUMBER: _ClassVar[int]
    CORECOUNTSET_FIELD_NUMBER: _ClassVar[int]
    CTCLASSNULL_FIELD_NUMBER: _ClassVar[int]
    CTCLASSSET_FIELD_NUMBER: _ClassVar[int]
    KNEEPOINTVOLTAGENULL_FIELD_NUMBER: _ClassVar[int]
    KNEEPOINTVOLTAGESET_FIELD_NUMBER: _ClassVar[int]
    MAXRATIO_FIELD_NUMBER: _ClassVar[int]
    NOMINALRATIO_FIELD_NUMBER: _ClassVar[int]
    PRIMARYRATIONULL_FIELD_NUMBER: _ClassVar[int]
    PRIMARYRATIOSET_FIELD_NUMBER: _ClassVar[int]
    RATEDCURRENTNULL_FIELD_NUMBER: _ClassVar[int]
    RATEDCURRENTSET_FIELD_NUMBER: _ClassVar[int]
    SECONDARYFLSRATINGNULL_FIELD_NUMBER: _ClassVar[int]
    SECONDARYFLSRATINGSET_FIELD_NUMBER: _ClassVar[int]
    SECONDARYRATIONULL_FIELD_NUMBER: _ClassVar[int]
    SECONDARYRATIOSET_FIELD_NUMBER: _ClassVar[int]
    USAGENULL_FIELD_NUMBER: _ClassVar[int]
    USAGESET_FIELD_NUMBER: _ClassVar[int]
    ai: _AssetInfo_pb2.AssetInfo
    accuracyClassNull: _struct_pb2.NullValue
    accuracyClassSet: str
    accuracyLimitNull: _struct_pb2.NullValue
    accuracyLimitSet: float
    coreCountNull: _struct_pb2.NullValue
    coreCountSet: int
    ctClassNull: _struct_pb2.NullValue
    ctClassSet: str
    kneePointVoltageNull: _struct_pb2.NullValue
    kneePointVoltageSet: int
    maxRatio: _Ratio_pb2.Ratio
    nominalRatio: _Ratio_pb2.Ratio
    primaryRatioNull: _struct_pb2.NullValue
    primaryRatioSet: float
    ratedCurrentNull: _struct_pb2.NullValue
    ratedCurrentSet: int
    secondaryFlsRatingNull: _struct_pb2.NullValue
    secondaryFlsRatingSet: int
    secondaryRatioNull: _struct_pb2.NullValue
    secondaryRatioSet: float
    usageNull: _struct_pb2.NullValue
    usageSet: str
    def __init__(self, ai: _Optional[_Union[_AssetInfo_pb2.AssetInfo, _Mapping]] = ..., accuracyClassNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., accuracyClassSet: _Optional[str] = ..., accuracyLimitNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., accuracyLimitSet: _Optional[float] = ..., coreCountNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., coreCountSet: _Optional[int] = ..., ctClassNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., ctClassSet: _Optional[str] = ..., kneePointVoltageNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., kneePointVoltageSet: _Optional[int] = ..., maxRatio: _Optional[_Union[_Ratio_pb2.Ratio, _Mapping]] = ..., nominalRatio: _Optional[_Union[_Ratio_pb2.Ratio, _Mapping]] = ..., primaryRatioNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., primaryRatioSet: _Optional[float] = ..., ratedCurrentNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., ratedCurrentSet: _Optional[int] = ..., secondaryFlsRatingNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., secondaryFlsRatingSet: _Optional[int] = ..., secondaryRatioNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., secondaryRatioSet: _Optional[float] = ..., usageNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., usageSet: _Optional[str] = ...) -> None: ...
