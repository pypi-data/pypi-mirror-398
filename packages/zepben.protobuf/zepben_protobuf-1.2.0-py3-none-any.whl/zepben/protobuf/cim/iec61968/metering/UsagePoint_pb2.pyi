from zepben.protobuf.cim.extensions.iec61968.common import ContactDetails_pb2 as _ContactDetails_pb2
from zepben.protobuf.cim.iec61970.base.core import IdentifiedObject_pb2 as _IdentifiedObject_pb2
from zepben.protobuf.cim.iec61970.base.core import PhaseCode_pb2 as _PhaseCode_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class UsagePoint(_message.Message):
    __slots__ = ("io", "usagePointLocationMRID", "equipmentMRIDs", "endDeviceMRIDs", "isVirtualNull", "isVirtualSet", "connectionCategoryNull", "connectionCategorySet", "ratedPowerNull", "ratedPowerSet", "approvedInverterCapacityNull", "approvedInverterCapacitySet", "phaseCode", "contacts")
    IO_FIELD_NUMBER: _ClassVar[int]
    USAGEPOINTLOCATIONMRID_FIELD_NUMBER: _ClassVar[int]
    EQUIPMENTMRIDS_FIELD_NUMBER: _ClassVar[int]
    ENDDEVICEMRIDS_FIELD_NUMBER: _ClassVar[int]
    ISVIRTUALNULL_FIELD_NUMBER: _ClassVar[int]
    ISVIRTUALSET_FIELD_NUMBER: _ClassVar[int]
    CONNECTIONCATEGORYNULL_FIELD_NUMBER: _ClassVar[int]
    CONNECTIONCATEGORYSET_FIELD_NUMBER: _ClassVar[int]
    RATEDPOWERNULL_FIELD_NUMBER: _ClassVar[int]
    RATEDPOWERSET_FIELD_NUMBER: _ClassVar[int]
    APPROVEDINVERTERCAPACITYNULL_FIELD_NUMBER: _ClassVar[int]
    APPROVEDINVERTERCAPACITYSET_FIELD_NUMBER: _ClassVar[int]
    PHASECODE_FIELD_NUMBER: _ClassVar[int]
    CONTACTS_FIELD_NUMBER: _ClassVar[int]
    io: _IdentifiedObject_pb2.IdentifiedObject
    usagePointLocationMRID: str
    equipmentMRIDs: _containers.RepeatedScalarFieldContainer[str]
    endDeviceMRIDs: _containers.RepeatedScalarFieldContainer[str]
    isVirtualNull: _struct_pb2.NullValue
    isVirtualSet: bool
    connectionCategoryNull: _struct_pb2.NullValue
    connectionCategorySet: str
    ratedPowerNull: _struct_pb2.NullValue
    ratedPowerSet: int
    approvedInverterCapacityNull: _struct_pb2.NullValue
    approvedInverterCapacitySet: int
    phaseCode: _PhaseCode_pb2.PhaseCode
    contacts: _containers.RepeatedCompositeFieldContainer[_ContactDetails_pb2.ContactDetails]
    def __init__(self, io: _Optional[_Union[_IdentifiedObject_pb2.IdentifiedObject, _Mapping]] = ..., usagePointLocationMRID: _Optional[str] = ..., equipmentMRIDs: _Optional[_Iterable[str]] = ..., endDeviceMRIDs: _Optional[_Iterable[str]] = ..., isVirtualNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., isVirtualSet: bool = ..., connectionCategoryNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., connectionCategorySet: _Optional[str] = ..., ratedPowerNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., ratedPowerSet: _Optional[int] = ..., approvedInverterCapacityNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., approvedInverterCapacitySet: _Optional[int] = ..., phaseCode: _Optional[_Union[_PhaseCode_pb2.PhaseCode, str]] = ..., contacts: _Optional[_Iterable[_Union[_ContactDetails_pb2.ContactDetails, _Mapping]]] = ...) -> None: ...
