from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DataSource(_message.Message):
    __slots__ = ("source", "version", "timestamp")
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    source: str
    version: str
    timestamp: _timestamp_pb2.Timestamp
    def __init__(self, source: _Optional[str] = ..., version: _Optional[str] = ..., timestamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class ServiceInfo(_message.Message):
    __slots__ = ("title", "version", "dataSources")
    TITLE_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    DATASOURCES_FIELD_NUMBER: _ClassVar[int]
    title: str
    version: str
    dataSources: _containers.RepeatedCompositeFieldContainer[DataSource]
    def __init__(self, title: _Optional[str] = ..., version: _Optional[str] = ..., dataSources: _Optional[_Iterable[_Union[DataSource, _Mapping]]] = ...) -> None: ...
