from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class NameType(_message.Message):
    __slots__ = ("name", "descriptionNull", "descriptionSet")
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTIONNULL_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTIONSET_FIELD_NUMBER: _ClassVar[int]
    name: str
    descriptionNull: _struct_pb2.NullValue
    descriptionSet: str
    def __init__(self, name: _Optional[str] = ..., descriptionNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., descriptionSet: _Optional[str] = ...) -> None: ...
