from zepben.protobuf.cim.iec61970.base.meas import MeasurementValue_pb2 as _MeasurementValue_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AnalogValue(_message.Message):
    __slots__ = ("mv", "analogMRID", "value")
    MV_FIELD_NUMBER: _ClassVar[int]
    ANALOGMRID_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    mv: _MeasurementValue_pb2.MeasurementValue
    analogMRID: str
    value: float
    def __init__(self, mv: _Optional[_Union[_MeasurementValue_pb2.MeasurementValue, _Mapping]] = ..., analogMRID: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
