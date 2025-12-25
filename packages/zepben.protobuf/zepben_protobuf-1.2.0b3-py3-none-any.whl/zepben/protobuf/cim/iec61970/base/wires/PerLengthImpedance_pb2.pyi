from zepben.protobuf.cim.iec61970.base.wires import PerLengthLineParameter_pb2 as _PerLengthLineParameter_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PerLengthImpedance(_message.Message):
    __slots__ = ("lp",)
    LP_FIELD_NUMBER: _ClassVar[int]
    lp: _PerLengthLineParameter_pb2.PerLengthLineParameter
    def __init__(self, lp: _Optional[_Union[_PerLengthLineParameter_pb2.PerLengthLineParameter, _Mapping]] = ...) -> None: ...
