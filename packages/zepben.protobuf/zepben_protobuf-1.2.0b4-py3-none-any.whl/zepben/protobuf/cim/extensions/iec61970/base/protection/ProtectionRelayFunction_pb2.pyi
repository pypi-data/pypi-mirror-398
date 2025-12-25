from zepben.protobuf.cim.extensions.iec61970.base.protection import RelaySetting_pb2 as _RelaySetting_pb2
from zepben.protobuf.cim.extensions.iec61970.base.protection import PowerDirectionKind_pb2 as _PowerDirectionKind_pb2
from zepben.protobuf.cim.extensions.iec61970.base.protection import ProtectionKind_pb2 as _ProtectionKind_pb2
from zepben.protobuf.cim.iec61970.base.core import PowerSystemResource_pb2 as _PowerSystemResource_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ProtectionRelayFunction(_message.Message):
    __slots__ = ("psr", "modelNull", "modelSet", "reclosingNull", "reclosingSet", "timeLimits", "thresholds", "relayDelayTimeNull", "relayDelayTimeSet", "protectionKind", "protectedSwitchMRIDs", "directableNull", "directableSet", "powerDirection", "sensorMRIDs", "schemeMRIDs")
    PSR_FIELD_NUMBER: _ClassVar[int]
    MODELNULL_FIELD_NUMBER: _ClassVar[int]
    MODELSET_FIELD_NUMBER: _ClassVar[int]
    RECLOSINGNULL_FIELD_NUMBER: _ClassVar[int]
    RECLOSINGSET_FIELD_NUMBER: _ClassVar[int]
    TIMELIMITS_FIELD_NUMBER: _ClassVar[int]
    THRESHOLDS_FIELD_NUMBER: _ClassVar[int]
    RELAYDELAYTIMENULL_FIELD_NUMBER: _ClassVar[int]
    RELAYDELAYTIMESET_FIELD_NUMBER: _ClassVar[int]
    PROTECTIONKIND_FIELD_NUMBER: _ClassVar[int]
    PROTECTEDSWITCHMRIDS_FIELD_NUMBER: _ClassVar[int]
    DIRECTABLENULL_FIELD_NUMBER: _ClassVar[int]
    DIRECTABLESET_FIELD_NUMBER: _ClassVar[int]
    POWERDIRECTION_FIELD_NUMBER: _ClassVar[int]
    SENSORMRIDS_FIELD_NUMBER: _ClassVar[int]
    SCHEMEMRIDS_FIELD_NUMBER: _ClassVar[int]
    psr: _PowerSystemResource_pb2.PowerSystemResource
    modelNull: _struct_pb2.NullValue
    modelSet: str
    reclosingNull: _struct_pb2.NullValue
    reclosingSet: bool
    timeLimits: _containers.RepeatedScalarFieldContainer[float]
    thresholds: _containers.RepeatedCompositeFieldContainer[_RelaySetting_pb2.RelaySetting]
    relayDelayTimeNull: _struct_pb2.NullValue
    relayDelayTimeSet: float
    protectionKind: _ProtectionKind_pb2.ProtectionKind
    protectedSwitchMRIDs: _containers.RepeatedScalarFieldContainer[str]
    directableNull: _struct_pb2.NullValue
    directableSet: bool
    powerDirection: _PowerDirectionKind_pb2.PowerDirectionKind
    sensorMRIDs: _containers.RepeatedScalarFieldContainer[str]
    schemeMRIDs: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, psr: _Optional[_Union[_PowerSystemResource_pb2.PowerSystemResource, _Mapping]] = ..., modelNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., modelSet: _Optional[str] = ..., reclosingNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., reclosingSet: bool = ..., timeLimits: _Optional[_Iterable[float]] = ..., thresholds: _Optional[_Iterable[_Union[_RelaySetting_pb2.RelaySetting, _Mapping]]] = ..., relayDelayTimeNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., relayDelayTimeSet: _Optional[float] = ..., protectionKind: _Optional[_Union[_ProtectionKind_pb2.ProtectionKind, str]] = ..., protectedSwitchMRIDs: _Optional[_Iterable[str]] = ..., directableNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., directableSet: bool = ..., powerDirection: _Optional[_Union[_PowerDirectionKind_pb2.PowerDirectionKind, str]] = ..., sensorMRIDs: _Optional[_Iterable[str]] = ..., schemeMRIDs: _Optional[_Iterable[str]] = ...) -> None: ...
