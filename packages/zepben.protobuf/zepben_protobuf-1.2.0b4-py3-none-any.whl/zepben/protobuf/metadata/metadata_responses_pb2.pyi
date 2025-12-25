from zepben.protobuf.metadata import metadata_data_pb2 as _metadata_data_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GetMetadataResponse(_message.Message):
    __slots__ = ("messageId", "serviceInfo")
    MESSAGEID_FIELD_NUMBER: _ClassVar[int]
    SERVICEINFO_FIELD_NUMBER: _ClassVar[int]
    messageId: int
    serviceInfo: _metadata_data_pb2.ServiceInfo
    def __init__(self, messageId: _Optional[int] = ..., serviceInfo: _Optional[_Union[_metadata_data_pb2.ServiceInfo, _Mapping]] = ...) -> None: ...
