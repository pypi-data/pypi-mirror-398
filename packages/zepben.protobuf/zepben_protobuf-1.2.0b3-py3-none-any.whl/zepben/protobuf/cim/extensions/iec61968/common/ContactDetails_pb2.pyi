from zepben.protobuf.cim.extensions.iec61968.common import ContactMethodType_pb2 as _ContactMethodType_pb2
from zepben.protobuf.cim.iec61968.common import ElectronicAddress_pb2 as _ElectronicAddress_pb2
from zepben.protobuf.cim.iec61968.common import StreetAddress_pb2 as _StreetAddress_pb2
from zepben.protobuf.cim.iec61968.common import TelephoneNumber_pb2 as _TelephoneNumber_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ContactDetails(_message.Message):
    __slots__ = ("id", "phoneNumbers", "contactAddress", "electronicAddresses", "contactTypeNull", "contactTypeSet", "firstNameNull", "firstNameSet", "lastNameNull", "lastNameSet", "preferredContactMethod", "isPrimaryNull", "isPrimarySet", "businessNameNull", "businessNameSet")
    ID_FIELD_NUMBER: _ClassVar[int]
    PHONENUMBERS_FIELD_NUMBER: _ClassVar[int]
    CONTACTADDRESS_FIELD_NUMBER: _ClassVar[int]
    ELECTRONICADDRESSES_FIELD_NUMBER: _ClassVar[int]
    CONTACTTYPENULL_FIELD_NUMBER: _ClassVar[int]
    CONTACTTYPESET_FIELD_NUMBER: _ClassVar[int]
    FIRSTNAMENULL_FIELD_NUMBER: _ClassVar[int]
    FIRSTNAMESET_FIELD_NUMBER: _ClassVar[int]
    LASTNAMENULL_FIELD_NUMBER: _ClassVar[int]
    LASTNAMESET_FIELD_NUMBER: _ClassVar[int]
    PREFERREDCONTACTMETHOD_FIELD_NUMBER: _ClassVar[int]
    ISPRIMARYNULL_FIELD_NUMBER: _ClassVar[int]
    ISPRIMARYSET_FIELD_NUMBER: _ClassVar[int]
    BUSINESSNAMENULL_FIELD_NUMBER: _ClassVar[int]
    BUSINESSNAMESET_FIELD_NUMBER: _ClassVar[int]
    id: str
    phoneNumbers: _containers.RepeatedCompositeFieldContainer[_TelephoneNumber_pb2.TelephoneNumber]
    contactAddress: _StreetAddress_pb2.StreetAddress
    electronicAddresses: _containers.RepeatedCompositeFieldContainer[_ElectronicAddress_pb2.ElectronicAddress]
    contactTypeNull: _struct_pb2.NullValue
    contactTypeSet: str
    firstNameNull: _struct_pb2.NullValue
    firstNameSet: str
    lastNameNull: _struct_pb2.NullValue
    lastNameSet: str
    preferredContactMethod: _ContactMethodType_pb2.ContactMethodType
    isPrimaryNull: _struct_pb2.NullValue
    isPrimarySet: bool
    businessNameNull: _struct_pb2.NullValue
    businessNameSet: str
    def __init__(self, id: _Optional[str] = ..., phoneNumbers: _Optional[_Iterable[_Union[_TelephoneNumber_pb2.TelephoneNumber, _Mapping]]] = ..., contactAddress: _Optional[_Union[_StreetAddress_pb2.StreetAddress, _Mapping]] = ..., electronicAddresses: _Optional[_Iterable[_Union[_ElectronicAddress_pb2.ElectronicAddress, _Mapping]]] = ..., contactTypeNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., contactTypeSet: _Optional[str] = ..., firstNameNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., firstNameSet: _Optional[str] = ..., lastNameNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., lastNameSet: _Optional[str] = ..., preferredContactMethod: _Optional[_Union[_ContactMethodType_pb2.ContactMethodType, str]] = ..., isPrimaryNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., isPrimarySet: bool = ..., businessNameNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., businessNameSet: _Optional[str] = ...) -> None: ...
