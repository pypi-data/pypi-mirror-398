from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class GetIdentifiedObjectsRequest(_message.Message):
    __slots__ = ("messageId", "mrids")
    MESSAGEID_FIELD_NUMBER: _ClassVar[int]
    MRIDS_FIELD_NUMBER: _ClassVar[int]
    messageId: int
    mrids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, messageId: _Optional[int] = ..., mrids: _Optional[_Iterable[str]] = ...) -> None: ...

class GetCustomersForContainerRequest(_message.Message):
    __slots__ = ("messageId", "mrids")
    MESSAGEID_FIELD_NUMBER: _ClassVar[int]
    MRIDS_FIELD_NUMBER: _ClassVar[int]
    messageId: int
    mrids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, messageId: _Optional[int] = ..., mrids: _Optional[_Iterable[str]] = ...) -> None: ...
