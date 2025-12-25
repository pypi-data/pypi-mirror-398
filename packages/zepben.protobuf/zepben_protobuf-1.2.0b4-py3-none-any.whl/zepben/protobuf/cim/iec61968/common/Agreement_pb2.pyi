from zepben.protobuf.cim.iec61968.common import Document_pb2 as _Document_pb2
from zepben.protobuf.cim.iec61970.base.domain import DateTimeInterval_pb2 as _DateTimeInterval_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Agreement(_message.Message):
    __slots__ = ("doc", "validityIntervalNull", "validityIntervalSet")
    DOC_FIELD_NUMBER: _ClassVar[int]
    VALIDITYINTERVALNULL_FIELD_NUMBER: _ClassVar[int]
    VALIDITYINTERVALSET_FIELD_NUMBER: _ClassVar[int]
    doc: _Document_pb2.Document
    validityIntervalNull: _struct_pb2.NullValue
    validityIntervalSet: _DateTimeInterval_pb2.DateTimeInterval
    def __init__(self, doc: _Optional[_Union[_Document_pb2.Document, _Mapping]] = ..., validityIntervalNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., validityIntervalSet: _Optional[_Union[_DateTimeInterval_pb2.DateTimeInterval, _Mapping]] = ...) -> None: ...
