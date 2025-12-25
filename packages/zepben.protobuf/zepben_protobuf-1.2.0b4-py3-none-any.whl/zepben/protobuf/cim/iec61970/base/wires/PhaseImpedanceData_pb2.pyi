from zepben.protobuf.cim.iec61970.base.wires import SinglePhaseKind_pb2 as _SinglePhaseKind_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PhaseImpedanceData(_message.Message):
    __slots__ = ("bNull", "bSet", "fromPhase", "toPhase", "gNull", "gSet", "rNull", "rSet", "xNull", "xSet")
    BNULL_FIELD_NUMBER: _ClassVar[int]
    BSET_FIELD_NUMBER: _ClassVar[int]
    FROMPHASE_FIELD_NUMBER: _ClassVar[int]
    TOPHASE_FIELD_NUMBER: _ClassVar[int]
    GNULL_FIELD_NUMBER: _ClassVar[int]
    GSET_FIELD_NUMBER: _ClassVar[int]
    RNULL_FIELD_NUMBER: _ClassVar[int]
    RSET_FIELD_NUMBER: _ClassVar[int]
    XNULL_FIELD_NUMBER: _ClassVar[int]
    XSET_FIELD_NUMBER: _ClassVar[int]
    bNull: _struct_pb2.NullValue
    bSet: float
    fromPhase: _SinglePhaseKind_pb2.SinglePhaseKind
    toPhase: _SinglePhaseKind_pb2.SinglePhaseKind
    gNull: _struct_pb2.NullValue
    gSet: float
    rNull: _struct_pb2.NullValue
    rSet: float
    xNull: _struct_pb2.NullValue
    xSet: float
    def __init__(self, bNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., bSet: _Optional[float] = ..., fromPhase: _Optional[_Union[_SinglePhaseKind_pb2.SinglePhaseKind, str]] = ..., toPhase: _Optional[_Union[_SinglePhaseKind_pb2.SinglePhaseKind, str]] = ..., gNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., gSet: _Optional[float] = ..., rNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., rSet: _Optional[float] = ..., xNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., xSet: _Optional[float] = ...) -> None: ...
