from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ComplexResult(_message.Message):
    __slots__ = ("real", "imaginary")
    REAL_FIELD_NUMBER: _ClassVar[int]
    IMAGINARY_FIELD_NUMBER: _ClassVar[int]
    real: float
    imaginary: float
    def __init__(self, real: _Optional[float] = ..., imaginary: _Optional[float] = ...) -> None: ...

class SamplePointReport(_message.Message):
    __slots__ = ("sampleId", "hour", "voltageA", "voltageB", "voltageC", "currentA", "currentB", "currentC", "powerTotal")
    SAMPLEID_FIELD_NUMBER: _ClassVar[int]
    HOUR_FIELD_NUMBER: _ClassVar[int]
    VOLTAGEA_FIELD_NUMBER: _ClassVar[int]
    VOLTAGEB_FIELD_NUMBER: _ClassVar[int]
    VOLTAGEC_FIELD_NUMBER: _ClassVar[int]
    CURRENTA_FIELD_NUMBER: _ClassVar[int]
    CURRENTB_FIELD_NUMBER: _ClassVar[int]
    CURRENTC_FIELD_NUMBER: _ClassVar[int]
    POWERTOTAL_FIELD_NUMBER: _ClassVar[int]
    sampleId: str
    hour: float
    voltageA: ComplexResult
    voltageB: ComplexResult
    voltageC: ComplexResult
    currentA: ComplexResult
    currentB: ComplexResult
    currentC: ComplexResult
    powerTotal: ComplexResult
    def __init__(self, sampleId: _Optional[str] = ..., hour: _Optional[float] = ..., voltageA: _Optional[_Union[ComplexResult, _Mapping]] = ..., voltageB: _Optional[_Union[ComplexResult, _Mapping]] = ..., voltageC: _Optional[_Union[ComplexResult, _Mapping]] = ..., currentA: _Optional[_Union[ComplexResult, _Mapping]] = ..., currentB: _Optional[_Union[ComplexResult, _Mapping]] = ..., currentC: _Optional[_Union[ComplexResult, _Mapping]] = ..., powerTotal: _Optional[_Union[ComplexResult, _Mapping]] = ...) -> None: ...
