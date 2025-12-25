from zepben.protobuf.cim.iec61970.base.meas import MeasurementValue_pb2 as _MeasurementValue_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AccumulatorValue(_message.Message):
    __slots__ = ("mv", "accumulatorMRID", "value")
    MV_FIELD_NUMBER: _ClassVar[int]
    ACCUMULATORMRID_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    mv: _MeasurementValue_pb2.MeasurementValue
    accumulatorMRID: str
    value: int
    def __init__(self, mv: _Optional[_Union[_MeasurementValue_pb2.MeasurementValue, _Mapping]] = ..., accumulatorMRID: _Optional[str] = ..., value: _Optional[int] = ...) -> None: ...
