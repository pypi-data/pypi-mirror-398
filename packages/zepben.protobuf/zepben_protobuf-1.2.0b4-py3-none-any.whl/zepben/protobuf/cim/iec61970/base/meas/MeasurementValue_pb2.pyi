from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class MeasurementValue(_message.Message):
    __slots__ = ("timeStampNull", "timeStampSet")
    TIMESTAMPNULL_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMPSET_FIELD_NUMBER: _ClassVar[int]
    timeStampNull: _struct_pb2.NullValue
    timeStampSet: _timestamp_pb2.Timestamp
    def __init__(self, timeStampNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., timeStampSet: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...
