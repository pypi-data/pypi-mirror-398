from zepben.protobuf.cim.iec61970.base.wires import PerLengthImpedance_pb2 as _PerLengthImpedance_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PerLengthSequenceImpedance(_message.Message):
    __slots__ = ("pli", "rNull", "rSet", "xNull", "xSet", "r0Null", "r0Set", "x0Null", "x0Set", "bchNull", "bchSet", "b0chNull", "b0chSet", "gchNull", "gchSet", "g0chNull", "g0chSet")
    PLI_FIELD_NUMBER: _ClassVar[int]
    RNULL_FIELD_NUMBER: _ClassVar[int]
    RSET_FIELD_NUMBER: _ClassVar[int]
    XNULL_FIELD_NUMBER: _ClassVar[int]
    XSET_FIELD_NUMBER: _ClassVar[int]
    R0NULL_FIELD_NUMBER: _ClassVar[int]
    R0SET_FIELD_NUMBER: _ClassVar[int]
    X0NULL_FIELD_NUMBER: _ClassVar[int]
    X0SET_FIELD_NUMBER: _ClassVar[int]
    BCHNULL_FIELD_NUMBER: _ClassVar[int]
    BCHSET_FIELD_NUMBER: _ClassVar[int]
    B0CHNULL_FIELD_NUMBER: _ClassVar[int]
    B0CHSET_FIELD_NUMBER: _ClassVar[int]
    GCHNULL_FIELD_NUMBER: _ClassVar[int]
    GCHSET_FIELD_NUMBER: _ClassVar[int]
    G0CHNULL_FIELD_NUMBER: _ClassVar[int]
    G0CHSET_FIELD_NUMBER: _ClassVar[int]
    pli: _PerLengthImpedance_pb2.PerLengthImpedance
    rNull: _struct_pb2.NullValue
    rSet: float
    xNull: _struct_pb2.NullValue
    xSet: float
    r0Null: _struct_pb2.NullValue
    r0Set: float
    x0Null: _struct_pb2.NullValue
    x0Set: float
    bchNull: _struct_pb2.NullValue
    bchSet: float
    b0chNull: _struct_pb2.NullValue
    b0chSet: float
    gchNull: _struct_pb2.NullValue
    gchSet: float
    g0chNull: _struct_pb2.NullValue
    g0chSet: float
    def __init__(self, pli: _Optional[_Union[_PerLengthImpedance_pb2.PerLengthImpedance, _Mapping]] = ..., rNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., rSet: _Optional[float] = ..., xNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., xSet: _Optional[float] = ..., r0Null: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., r0Set: _Optional[float] = ..., x0Null: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., x0Set: _Optional[float] = ..., bchNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., bchSet: _Optional[float] = ..., b0chNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., b0chSet: _Optional[float] = ..., gchNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., gchSet: _Optional[float] = ..., g0chNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., g0chSet: _Optional[float] = ...) -> None: ...
