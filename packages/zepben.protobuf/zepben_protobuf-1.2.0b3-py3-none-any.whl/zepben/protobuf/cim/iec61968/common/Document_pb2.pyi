from google.protobuf import timestamp_pb2 as _timestamp_pb2
from zepben.protobuf.cim.iec61970.base.core import IdentifiedObject_pb2 as _IdentifiedObject_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Document(_message.Message):
    __slots__ = ("io", "titleNull", "titleSet", "createdDateTimeNull", "createdDateTimeSet", "authorNameNull", "authorNameSet", "typeNull", "typeSet", "statusNull", "statusSet", "commentNull", "commentSet")
    IO_FIELD_NUMBER: _ClassVar[int]
    TITLENULL_FIELD_NUMBER: _ClassVar[int]
    TITLESET_FIELD_NUMBER: _ClassVar[int]
    CREATEDDATETIMENULL_FIELD_NUMBER: _ClassVar[int]
    CREATEDDATETIMESET_FIELD_NUMBER: _ClassVar[int]
    AUTHORNAMENULL_FIELD_NUMBER: _ClassVar[int]
    AUTHORNAMESET_FIELD_NUMBER: _ClassVar[int]
    TYPENULL_FIELD_NUMBER: _ClassVar[int]
    TYPESET_FIELD_NUMBER: _ClassVar[int]
    STATUSNULL_FIELD_NUMBER: _ClassVar[int]
    STATUSSET_FIELD_NUMBER: _ClassVar[int]
    COMMENTNULL_FIELD_NUMBER: _ClassVar[int]
    COMMENTSET_FIELD_NUMBER: _ClassVar[int]
    io: _IdentifiedObject_pb2.IdentifiedObject
    titleNull: _struct_pb2.NullValue
    titleSet: str
    createdDateTimeNull: _struct_pb2.NullValue
    createdDateTimeSet: _timestamp_pb2.Timestamp
    authorNameNull: _struct_pb2.NullValue
    authorNameSet: str
    typeNull: _struct_pb2.NullValue
    typeSet: str
    statusNull: _struct_pb2.NullValue
    statusSet: str
    commentNull: _struct_pb2.NullValue
    commentSet: str
    def __init__(self, io: _Optional[_Union[_IdentifiedObject_pb2.IdentifiedObject, _Mapping]] = ..., titleNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., titleSet: _Optional[str] = ..., createdDateTimeNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., createdDateTimeSet: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., authorNameNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., authorNameSet: _Optional[str] = ..., typeNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., typeSet: _Optional[str] = ..., statusNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., statusSet: _Optional[str] = ..., commentNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., commentSet: _Optional[str] = ...) -> None: ...
