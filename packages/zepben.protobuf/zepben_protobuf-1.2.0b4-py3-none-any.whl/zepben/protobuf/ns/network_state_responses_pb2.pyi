from zepben.protobuf.ns.data import change_status_pb2 as _change_status_pb2
from zepben.protobuf.ns.data import change_events_pb2 as _change_events_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SetCurrentStatesResponse(_message.Message):
    __slots__ = ("messageId", "success", "failure", "notProcessed")
    MESSAGEID_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    FAILURE_FIELD_NUMBER: _ClassVar[int]
    NOTPROCESSED_FIELD_NUMBER: _ClassVar[int]
    messageId: int
    success: _change_status_pb2.BatchSuccessful
    failure: _change_status_pb2.BatchFailure
    notProcessed: _change_status_pb2.BatchNotProcessed
    def __init__(self, messageId: _Optional[int] = ..., success: _Optional[_Union[_change_status_pb2.BatchSuccessful, _Mapping]] = ..., failure: _Optional[_Union[_change_status_pb2.BatchFailure, _Mapping]] = ..., notProcessed: _Optional[_Union[_change_status_pb2.BatchNotProcessed, _Mapping]] = ...) -> None: ...

class GetCurrentStatesResponse(_message.Message):
    __slots__ = ("messageId", "event")
    MESSAGEID_FIELD_NUMBER: _ClassVar[int]
    EVENT_FIELD_NUMBER: _ClassVar[int]
    messageId: int
    event: _containers.RepeatedCompositeFieldContainer[_change_events_pb2.CurrentStateEvent]
    def __init__(self, messageId: _Optional[int] = ..., event: _Optional[_Iterable[_Union[_change_events_pb2.CurrentStateEvent, _Mapping]]] = ...) -> None: ...
