from zepben.protobuf.cim.iec61968.assets import AssetInfo_pb2 as _AssetInfo_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ShuntCompensatorInfo(_message.Message):
    __slots__ = ("ai", "maxPowerLossNull", "maxPowerLossSet", "ratedCurrentNull", "ratedCurrentSet", "ratedReactivePowerNull", "ratedReactivePowerSet", "ratedVoltageNull", "ratedVoltageSet")
    AI_FIELD_NUMBER: _ClassVar[int]
    MAXPOWERLOSSNULL_FIELD_NUMBER: _ClassVar[int]
    MAXPOWERLOSSSET_FIELD_NUMBER: _ClassVar[int]
    RATEDCURRENTNULL_FIELD_NUMBER: _ClassVar[int]
    RATEDCURRENTSET_FIELD_NUMBER: _ClassVar[int]
    RATEDREACTIVEPOWERNULL_FIELD_NUMBER: _ClassVar[int]
    RATEDREACTIVEPOWERSET_FIELD_NUMBER: _ClassVar[int]
    RATEDVOLTAGENULL_FIELD_NUMBER: _ClassVar[int]
    RATEDVOLTAGESET_FIELD_NUMBER: _ClassVar[int]
    ai: _AssetInfo_pb2.AssetInfo
    maxPowerLossNull: _struct_pb2.NullValue
    maxPowerLossSet: int
    ratedCurrentNull: _struct_pb2.NullValue
    ratedCurrentSet: int
    ratedReactivePowerNull: _struct_pb2.NullValue
    ratedReactivePowerSet: int
    ratedVoltageNull: _struct_pb2.NullValue
    ratedVoltageSet: int
    def __init__(self, ai: _Optional[_Union[_AssetInfo_pb2.AssetInfo, _Mapping]] = ..., maxPowerLossNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., maxPowerLossSet: _Optional[int] = ..., ratedCurrentNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., ratedCurrentSet: _Optional[int] = ..., ratedReactivePowerNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., ratedReactivePowerSet: _Optional[int] = ..., ratedVoltageNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., ratedVoltageSet: _Optional[int] = ...) -> None: ...
