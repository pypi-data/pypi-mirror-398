from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from typing import ClassVar as _ClassVar

DESCRIPTOR: _descriptor.FileDescriptor

class ContactMethodType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CONTACT_METHOD_TYPE_UNKNOWN: _ClassVar[ContactMethodType]
    CONTACT_METHOD_TYPE_EMAIL: _ClassVar[ContactMethodType]
    CONTACT_METHOD_TYPE_CALL: _ClassVar[ContactMethodType]
    CONTACT_METHOD_TYPE_LETTER: _ClassVar[ContactMethodType]
CONTACT_METHOD_TYPE_UNKNOWN: ContactMethodType
CONTACT_METHOD_TYPE_EMAIL: ContactMethodType
CONTACT_METHOD_TYPE_CALL: ContactMethodType
CONTACT_METHOD_TYPE_LETTER: ContactMethodType
