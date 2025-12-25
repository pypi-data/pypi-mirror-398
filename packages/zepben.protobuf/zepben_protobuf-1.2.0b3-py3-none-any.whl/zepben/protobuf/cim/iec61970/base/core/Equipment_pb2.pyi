from zepben.protobuf.cim.iec61970.base.core import PowerSystemResource_pb2 as _PowerSystemResource_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Equipment(_message.Message):
    __slots__ = ("psr", "inService", "normallyInService", "equipmentContainerMRIDs", "usagePointMRIDs", "operationalRestrictionMRIDs", "currentContainerMRIDs", "commissionedDateNull", "commissionedDateSet")
    PSR_FIELD_NUMBER: _ClassVar[int]
    INSERVICE_FIELD_NUMBER: _ClassVar[int]
    NORMALLYINSERVICE_FIELD_NUMBER: _ClassVar[int]
    EQUIPMENTCONTAINERMRIDS_FIELD_NUMBER: _ClassVar[int]
    USAGEPOINTMRIDS_FIELD_NUMBER: _ClassVar[int]
    OPERATIONALRESTRICTIONMRIDS_FIELD_NUMBER: _ClassVar[int]
    CURRENTCONTAINERMRIDS_FIELD_NUMBER: _ClassVar[int]
    COMMISSIONEDDATENULL_FIELD_NUMBER: _ClassVar[int]
    COMMISSIONEDDATESET_FIELD_NUMBER: _ClassVar[int]
    psr: _PowerSystemResource_pb2.PowerSystemResource
    inService: bool
    normallyInService: bool
    equipmentContainerMRIDs: _containers.RepeatedScalarFieldContainer[str]
    usagePointMRIDs: _containers.RepeatedScalarFieldContainer[str]
    operationalRestrictionMRIDs: _containers.RepeatedScalarFieldContainer[str]
    currentContainerMRIDs: _containers.RepeatedScalarFieldContainer[str]
    commissionedDateNull: _struct_pb2.NullValue
    commissionedDateSet: _timestamp_pb2.Timestamp
    def __init__(self, psr: _Optional[_Union[_PowerSystemResource_pb2.PowerSystemResource, _Mapping]] = ..., inService: bool = ..., normallyInService: bool = ..., equipmentContainerMRIDs: _Optional[_Iterable[str]] = ..., usagePointMRIDs: _Optional[_Iterable[str]] = ..., operationalRestrictionMRIDs: _Optional[_Iterable[str]] = ..., currentContainerMRIDs: _Optional[_Iterable[str]] = ..., commissionedDateNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., commissionedDateSet: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...
