from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class LoadShape(_message.Message):
    __slots__ = ("id", "hrInterval", "pValues", "qValues", "normalise")
    ID_FIELD_NUMBER: _ClassVar[int]
    HRINTERVAL_FIELD_NUMBER: _ClassVar[int]
    PVALUES_FIELD_NUMBER: _ClassVar[int]
    QVALUES_FIELD_NUMBER: _ClassVar[int]
    NORMALISE_FIELD_NUMBER: _ClassVar[int]
    id: str
    hrInterval: float
    pValues: _containers.RepeatedScalarFieldContainer[float]
    qValues: _containers.RepeatedScalarFieldContainer[float]
    normalise: bool
    def __init__(self, id: _Optional[str] = ..., hrInterval: _Optional[float] = ..., pValues: _Optional[_Iterable[float]] = ..., qValues: _Optional[_Iterable[float]] = ..., normalise: bool = ...) -> None: ...
