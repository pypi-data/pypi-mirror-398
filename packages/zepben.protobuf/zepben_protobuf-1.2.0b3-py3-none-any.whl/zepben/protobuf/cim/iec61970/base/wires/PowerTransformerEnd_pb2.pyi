from zepben.protobuf.cim.extensions.iec61970.base.wires import TransformerEndRatedS_pb2 as _TransformerEndRatedS_pb2
from zepben.protobuf.cim.iec61970.base.wires import TransformerEnd_pb2 as _TransformerEnd_pb2
from zepben.protobuf.cim.iec61970.base.wires import WindingConnection_pb2 as _WindingConnection_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PowerTransformerEnd(_message.Message):
    __slots__ = ("te", "powerTransformerMRID", "ratedSNull", "ratedSSet", "ratedUNull", "ratedUSet", "rNull", "rSet", "xNull", "xSet", "r0Null", "r0Set", "x0Null", "x0Set", "connectionKind", "bNull", "bSet", "b0Null", "b0Set", "gNull", "gSet", "g0Null", "g0Set", "phaseAngleClockNull", "phaseAngleClockSet", "ratings")
    TE_FIELD_NUMBER: _ClassVar[int]
    POWERTRANSFORMERMRID_FIELD_NUMBER: _ClassVar[int]
    RATEDSNULL_FIELD_NUMBER: _ClassVar[int]
    RATEDSSET_FIELD_NUMBER: _ClassVar[int]
    RATEDUNULL_FIELD_NUMBER: _ClassVar[int]
    RATEDUSET_FIELD_NUMBER: _ClassVar[int]
    RNULL_FIELD_NUMBER: _ClassVar[int]
    RSET_FIELD_NUMBER: _ClassVar[int]
    XNULL_FIELD_NUMBER: _ClassVar[int]
    XSET_FIELD_NUMBER: _ClassVar[int]
    R0NULL_FIELD_NUMBER: _ClassVar[int]
    R0SET_FIELD_NUMBER: _ClassVar[int]
    X0NULL_FIELD_NUMBER: _ClassVar[int]
    X0SET_FIELD_NUMBER: _ClassVar[int]
    CONNECTIONKIND_FIELD_NUMBER: _ClassVar[int]
    BNULL_FIELD_NUMBER: _ClassVar[int]
    BSET_FIELD_NUMBER: _ClassVar[int]
    B0NULL_FIELD_NUMBER: _ClassVar[int]
    B0SET_FIELD_NUMBER: _ClassVar[int]
    GNULL_FIELD_NUMBER: _ClassVar[int]
    GSET_FIELD_NUMBER: _ClassVar[int]
    G0NULL_FIELD_NUMBER: _ClassVar[int]
    G0SET_FIELD_NUMBER: _ClassVar[int]
    PHASEANGLECLOCKNULL_FIELD_NUMBER: _ClassVar[int]
    PHASEANGLECLOCKSET_FIELD_NUMBER: _ClassVar[int]
    RATINGS_FIELD_NUMBER: _ClassVar[int]
    te: _TransformerEnd_pb2.TransformerEnd
    powerTransformerMRID: str
    ratedSNull: _struct_pb2.NullValue
    ratedSSet: int
    ratedUNull: _struct_pb2.NullValue
    ratedUSet: int
    rNull: _struct_pb2.NullValue
    rSet: float
    xNull: _struct_pb2.NullValue
    xSet: float
    r0Null: _struct_pb2.NullValue
    r0Set: float
    x0Null: _struct_pb2.NullValue
    x0Set: float
    connectionKind: _WindingConnection_pb2.WindingConnection
    bNull: _struct_pb2.NullValue
    bSet: float
    b0Null: _struct_pb2.NullValue
    b0Set: float
    gNull: _struct_pb2.NullValue
    gSet: float
    g0Null: _struct_pb2.NullValue
    g0Set: float
    phaseAngleClockNull: _struct_pb2.NullValue
    phaseAngleClockSet: int
    ratings: _containers.RepeatedCompositeFieldContainer[_TransformerEndRatedS_pb2.TransformerEndRatedS]
    def __init__(self, te: _Optional[_Union[_TransformerEnd_pb2.TransformerEnd, _Mapping]] = ..., powerTransformerMRID: _Optional[str] = ..., ratedSNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., ratedSSet: _Optional[int] = ..., ratedUNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., ratedUSet: _Optional[int] = ..., rNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., rSet: _Optional[float] = ..., xNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., xSet: _Optional[float] = ..., r0Null: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., r0Set: _Optional[float] = ..., x0Null: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., x0Set: _Optional[float] = ..., connectionKind: _Optional[_Union[_WindingConnection_pb2.WindingConnection, str]] = ..., bNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., bSet: _Optional[float] = ..., b0Null: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., b0Set: _Optional[float] = ..., gNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., gSet: _Optional[float] = ..., g0Null: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., g0Set: _Optional[float] = ..., phaseAngleClockNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., phaseAngleClockSet: _Optional[int] = ..., ratings: _Optional[_Iterable[_Union[_TransformerEndRatedS_pb2.TransformerEndRatedS, _Mapping]]] = ...) -> None: ...
