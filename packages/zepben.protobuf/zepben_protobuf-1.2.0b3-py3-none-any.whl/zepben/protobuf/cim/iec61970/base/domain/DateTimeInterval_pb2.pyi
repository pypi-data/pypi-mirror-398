from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DateTimeInterval(_message.Message):
    __slots__ = ("endNull", "endSet", "startNull", "startSet")
    ENDNULL_FIELD_NUMBER: _ClassVar[int]
    ENDSET_FIELD_NUMBER: _ClassVar[int]
    STARTNULL_FIELD_NUMBER: _ClassVar[int]
    STARTSET_FIELD_NUMBER: _ClassVar[int]
    endNull: _struct_pb2.NullValue
    endSet: _timestamp_pb2.Timestamp
    startNull: _struct_pb2.NullValue
    startSet: _timestamp_pb2.Timestamp
    def __init__(self, endNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., endSet: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., startNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., startSet: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...
