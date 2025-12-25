from zepben.protobuf.cim.iec61970.base.meas import Measurement_pb2 as _Measurement_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Accumulator(_message.Message):
    __slots__ = ("measurement",)
    MEASUREMENT_FIELD_NUMBER: _ClassVar[int]
    measurement: _Measurement_pb2.Measurement
    def __init__(self, measurement: _Optional[_Union[_Measurement_pb2.Measurement, _Mapping]] = ...) -> None: ...
