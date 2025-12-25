from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class BatchSuccessful(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class BatchFailure(_message.Message):
    __slots__ = ("partialFailure", "failed")
    PARTIALFAILURE_FIELD_NUMBER: _ClassVar[int]
    FAILED_FIELD_NUMBER: _ClassVar[int]
    partialFailure: bool
    failed: _containers.RepeatedCompositeFieldContainer[StateEventFailure]
    def __init__(self, partialFailure: bool = ..., failed: _Optional[_Iterable[_Union[StateEventFailure, _Mapping]]] = ...) -> None: ...

class BatchNotProcessed(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class StateEventFailure(_message.Message):
    __slots__ = ("eventId", "message", "unknownMrid", "duplicateMrid", "invalidMrid", "unsupportedPhasing", "unsupportedMrid")
    EVENTID_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    UNKNOWNMRID_FIELD_NUMBER: _ClassVar[int]
    DUPLICATEMRID_FIELD_NUMBER: _ClassVar[int]
    INVALIDMRID_FIELD_NUMBER: _ClassVar[int]
    UNSUPPORTEDPHASING_FIELD_NUMBER: _ClassVar[int]
    UNSUPPORTEDMRID_FIELD_NUMBER: _ClassVar[int]
    eventId: str
    message: str
    unknownMrid: StateEventUnknownMrid
    duplicateMrid: StateEventDuplicateMrid
    invalidMrid: StateEventInvalidMrid
    unsupportedPhasing: StateEventUnsupportedPhasing
    unsupportedMrid: StateEventUnsupportedMrid
    def __init__(self, eventId: _Optional[str] = ..., message: _Optional[str] = ..., unknownMrid: _Optional[_Union[StateEventUnknownMrid, _Mapping]] = ..., duplicateMrid: _Optional[_Union[StateEventDuplicateMrid, _Mapping]] = ..., invalidMrid: _Optional[_Union[StateEventInvalidMrid, _Mapping]] = ..., unsupportedPhasing: _Optional[_Union[StateEventUnsupportedPhasing, _Mapping]] = ..., unsupportedMrid: _Optional[_Union[StateEventUnsupportedMrid, _Mapping]] = ...) -> None: ...

class StateEventUnknownMrid(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class StateEventDuplicateMrid(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class StateEventInvalidMrid(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class StateEventUnsupportedPhasing(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class StateEventUnsupportedMrid(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...
