from zepben.protobuf.cim.iec61968.common import Document_pb2 as _Document_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class OperationalRestriction(_message.Message):
    __slots__ = ("doc",)
    DOC_FIELD_NUMBER: _ClassVar[int]
    doc: _Document_pb2.Document
    def __init__(self, doc: _Optional[_Union[_Document_pb2.Document, _Mapping]] = ...) -> None: ...
