from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ElectronicAddress(_message.Message):
    __slots__ = ("email1Null", "email1Set", "isPrimaryNull", "isPrimarySet", "descriptionNull", "descriptionSet")
    EMAIL1NULL_FIELD_NUMBER: _ClassVar[int]
    EMAIL1SET_FIELD_NUMBER: _ClassVar[int]
    ISPRIMARYNULL_FIELD_NUMBER: _ClassVar[int]
    ISPRIMARYSET_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTIONNULL_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTIONSET_FIELD_NUMBER: _ClassVar[int]
    email1Null: _struct_pb2.NullValue
    email1Set: str
    isPrimaryNull: _struct_pb2.NullValue
    isPrimarySet: bool
    descriptionNull: _struct_pb2.NullValue
    descriptionSet: str
    def __init__(self, email1Null: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., email1Set: _Optional[str] = ..., isPrimaryNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., isPrimarySet: bool = ..., descriptionNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., descriptionSet: _Optional[str] = ...) -> None: ...
