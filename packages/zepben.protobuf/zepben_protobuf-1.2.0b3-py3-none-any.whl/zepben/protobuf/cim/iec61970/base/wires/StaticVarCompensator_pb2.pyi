from zepben.protobuf.cim.iec61970.base.wires import RegulatingCondEq_pb2 as _RegulatingCondEq_pb2
from zepben.protobuf.cim.iec61970.base.wires import SVCControlMode_pb2 as _SVCControlMode_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class StaticVarCompensator(_message.Message):
    __slots__ = ("rce", "capacitiveRatingNull", "capacitiveRatingSet", "inductiveRatingNull", "inductiveRatingSet", "qNull", "qSet", "svcControlMode", "voltageSetPointNull", "voltageSetPointSet")
    RCE_FIELD_NUMBER: _ClassVar[int]
    CAPACITIVERATINGNULL_FIELD_NUMBER: _ClassVar[int]
    CAPACITIVERATINGSET_FIELD_NUMBER: _ClassVar[int]
    INDUCTIVERATINGNULL_FIELD_NUMBER: _ClassVar[int]
    INDUCTIVERATINGSET_FIELD_NUMBER: _ClassVar[int]
    QNULL_FIELD_NUMBER: _ClassVar[int]
    QSET_FIELD_NUMBER: _ClassVar[int]
    SVCCONTROLMODE_FIELD_NUMBER: _ClassVar[int]
    VOLTAGESETPOINTNULL_FIELD_NUMBER: _ClassVar[int]
    VOLTAGESETPOINTSET_FIELD_NUMBER: _ClassVar[int]
    rce: _RegulatingCondEq_pb2.RegulatingCondEq
    capacitiveRatingNull: _struct_pb2.NullValue
    capacitiveRatingSet: float
    inductiveRatingNull: _struct_pb2.NullValue
    inductiveRatingSet: float
    qNull: _struct_pb2.NullValue
    qSet: float
    svcControlMode: _SVCControlMode_pb2.SVCControlMode
    voltageSetPointNull: _struct_pb2.NullValue
    voltageSetPointSet: int
    def __init__(self, rce: _Optional[_Union[_RegulatingCondEq_pb2.RegulatingCondEq, _Mapping]] = ..., capacitiveRatingNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., capacitiveRatingSet: _Optional[float] = ..., inductiveRatingNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., inductiveRatingSet: _Optional[float] = ..., qNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., qSet: _Optional[float] = ..., svcControlMode: _Optional[_Union[_SVCControlMode_pb2.SVCControlMode, str]] = ..., voltageSetPointNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., voltageSetPointSet: _Optional[int] = ...) -> None: ...
