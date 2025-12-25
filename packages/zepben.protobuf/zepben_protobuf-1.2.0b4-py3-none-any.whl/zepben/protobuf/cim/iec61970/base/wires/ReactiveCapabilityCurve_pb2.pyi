from zepben.protobuf.cim.iec61970.base.core import Curve_pb2 as _Curve_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ReactiveCapabilityCurve(_message.Message):
    __slots__ = ("c",)
    C_FIELD_NUMBER: _ClassVar[int]
    c: _Curve_pb2.Curve
    def __init__(self, c: _Optional[_Union[_Curve_pb2.Curve, _Mapping]] = ...) -> None: ...
