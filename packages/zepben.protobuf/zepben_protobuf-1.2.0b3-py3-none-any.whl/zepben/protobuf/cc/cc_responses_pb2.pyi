from zepben.protobuf.cc import cc_data_pb2 as _cc_data_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GetIdentifiedObjectsResponse(_message.Message):
    __slots__ = ("messageId", "identifiedObjects")
    MESSAGEID_FIELD_NUMBER: _ClassVar[int]
    IDENTIFIEDOBJECTS_FIELD_NUMBER: _ClassVar[int]
    messageId: int
    identifiedObjects: _containers.RepeatedCompositeFieldContainer[_cc_data_pb2.CustomerIdentifiedObject]
    def __init__(self, messageId: _Optional[int] = ..., identifiedObjects: _Optional[_Iterable[_Union[_cc_data_pb2.CustomerIdentifiedObject, _Mapping]]] = ...) -> None: ...

class GetCustomersForContainerResponse(_message.Message):
    __slots__ = ("messageId", "identifiedObjects")
    MESSAGEID_FIELD_NUMBER: _ClassVar[int]
    IDENTIFIEDOBJECTS_FIELD_NUMBER: _ClassVar[int]
    messageId: int
    identifiedObjects: _containers.RepeatedCompositeFieldContainer[_cc_data_pb2.CustomerIdentifiedObject]
    def __init__(self, messageId: _Optional[int] = ..., identifiedObjects: _Optional[_Iterable[_Union[_cc_data_pb2.CustomerIdentifiedObject, _Mapping]]] = ...) -> None: ...
