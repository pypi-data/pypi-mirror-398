from zepben.protobuf.cim.extensions.iec61970.base.protection import PolarizingQuantityType_pb2 as _PolarizingQuantityType_pb2
from zepben.protobuf.cim.extensions.iec61970.base.protection import ProtectionRelayFunction_pb2 as _ProtectionRelayFunction_pb2
from zepben.protobuf.cim.iec61970.base.core import PhaseCode_pb2 as _PhaseCode_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DirectionalCurrentRelay(_message.Message):
    __slots__ = ("prf", "directionalCharacteristicAngleNull", "directionalCharacteristicAngleSet", "polarizingQuantityType", "relayElementPhase", "minimumPickupCurrentNull", "minimumPickupCurrentSet", "currentLimit1Null", "currentLimit1Set", "inverseTimeFlagNull", "inverseTimeFlagSet", "timeDelay1Null", "timeDelay1Set")
    PRF_FIELD_NUMBER: _ClassVar[int]
    DIRECTIONALCHARACTERISTICANGLENULL_FIELD_NUMBER: _ClassVar[int]
    DIRECTIONALCHARACTERISTICANGLESET_FIELD_NUMBER: _ClassVar[int]
    POLARIZINGQUANTITYTYPE_FIELD_NUMBER: _ClassVar[int]
    RELAYELEMENTPHASE_FIELD_NUMBER: _ClassVar[int]
    MINIMUMPICKUPCURRENTNULL_FIELD_NUMBER: _ClassVar[int]
    MINIMUMPICKUPCURRENTSET_FIELD_NUMBER: _ClassVar[int]
    CURRENTLIMIT1NULL_FIELD_NUMBER: _ClassVar[int]
    CURRENTLIMIT1SET_FIELD_NUMBER: _ClassVar[int]
    INVERSETIMEFLAGNULL_FIELD_NUMBER: _ClassVar[int]
    INVERSETIMEFLAGSET_FIELD_NUMBER: _ClassVar[int]
    TIMEDELAY1NULL_FIELD_NUMBER: _ClassVar[int]
    TIMEDELAY1SET_FIELD_NUMBER: _ClassVar[int]
    prf: _ProtectionRelayFunction_pb2.ProtectionRelayFunction
    directionalCharacteristicAngleNull: _struct_pb2.NullValue
    directionalCharacteristicAngleSet: float
    polarizingQuantityType: _PolarizingQuantityType_pb2.PolarizingQuantityType
    relayElementPhase: _PhaseCode_pb2.PhaseCode
    minimumPickupCurrentNull: _struct_pb2.NullValue
    minimumPickupCurrentSet: float
    currentLimit1Null: _struct_pb2.NullValue
    currentLimit1Set: float
    inverseTimeFlagNull: _struct_pb2.NullValue
    inverseTimeFlagSet: bool
    timeDelay1Null: _struct_pb2.NullValue
    timeDelay1Set: float
    def __init__(self, prf: _Optional[_Union[_ProtectionRelayFunction_pb2.ProtectionRelayFunction, _Mapping]] = ..., directionalCharacteristicAngleNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., directionalCharacteristicAngleSet: _Optional[float] = ..., polarizingQuantityType: _Optional[_Union[_PolarizingQuantityType_pb2.PolarizingQuantityType, str]] = ..., relayElementPhase: _Optional[_Union[_PhaseCode_pb2.PhaseCode, str]] = ..., minimumPickupCurrentNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., minimumPickupCurrentSet: _Optional[float] = ..., currentLimit1Null: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., currentLimit1Set: _Optional[float] = ..., inverseTimeFlagNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., inverseTimeFlagSet: bool = ..., timeDelay1Null: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., timeDelay1Set: _Optional[float] = ...) -> None: ...
