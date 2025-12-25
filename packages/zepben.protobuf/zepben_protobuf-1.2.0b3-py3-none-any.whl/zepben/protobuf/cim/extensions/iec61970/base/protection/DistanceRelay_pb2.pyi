from zepben.protobuf.cim.extensions.iec61970.base.protection import ProtectionRelayFunction_pb2 as _ProtectionRelayFunction_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DistanceRelay(_message.Message):
    __slots__ = ("prf", "backwardBlindNull", "backwardBlindSet", "backwardReachNull", "backwardReachSet", "backwardReactanceNull", "backwardReactanceSet", "forwardBlindNull", "forwardBlindSet", "forwardReachNull", "forwardReachSet", "forwardReactanceNull", "forwardReactanceSet", "operationPhaseAngle1Null", "operationPhaseAngle1Set", "operationPhaseAngle2Null", "operationPhaseAngle2Set", "operationPhaseAngle3Null", "operationPhaseAngle3Set")
    PRF_FIELD_NUMBER: _ClassVar[int]
    BACKWARDBLINDNULL_FIELD_NUMBER: _ClassVar[int]
    BACKWARDBLINDSET_FIELD_NUMBER: _ClassVar[int]
    BACKWARDREACHNULL_FIELD_NUMBER: _ClassVar[int]
    BACKWARDREACHSET_FIELD_NUMBER: _ClassVar[int]
    BACKWARDREACTANCENULL_FIELD_NUMBER: _ClassVar[int]
    BACKWARDREACTANCESET_FIELD_NUMBER: _ClassVar[int]
    FORWARDBLINDNULL_FIELD_NUMBER: _ClassVar[int]
    FORWARDBLINDSET_FIELD_NUMBER: _ClassVar[int]
    FORWARDREACHNULL_FIELD_NUMBER: _ClassVar[int]
    FORWARDREACHSET_FIELD_NUMBER: _ClassVar[int]
    FORWARDREACTANCENULL_FIELD_NUMBER: _ClassVar[int]
    FORWARDREACTANCESET_FIELD_NUMBER: _ClassVar[int]
    OPERATIONPHASEANGLE1NULL_FIELD_NUMBER: _ClassVar[int]
    OPERATIONPHASEANGLE1SET_FIELD_NUMBER: _ClassVar[int]
    OPERATIONPHASEANGLE2NULL_FIELD_NUMBER: _ClassVar[int]
    OPERATIONPHASEANGLE2SET_FIELD_NUMBER: _ClassVar[int]
    OPERATIONPHASEANGLE3NULL_FIELD_NUMBER: _ClassVar[int]
    OPERATIONPHASEANGLE3SET_FIELD_NUMBER: _ClassVar[int]
    prf: _ProtectionRelayFunction_pb2.ProtectionRelayFunction
    backwardBlindNull: _struct_pb2.NullValue
    backwardBlindSet: float
    backwardReachNull: _struct_pb2.NullValue
    backwardReachSet: float
    backwardReactanceNull: _struct_pb2.NullValue
    backwardReactanceSet: float
    forwardBlindNull: _struct_pb2.NullValue
    forwardBlindSet: float
    forwardReachNull: _struct_pb2.NullValue
    forwardReachSet: float
    forwardReactanceNull: _struct_pb2.NullValue
    forwardReactanceSet: float
    operationPhaseAngle1Null: _struct_pb2.NullValue
    operationPhaseAngle1Set: float
    operationPhaseAngle2Null: _struct_pb2.NullValue
    operationPhaseAngle2Set: float
    operationPhaseAngle3Null: _struct_pb2.NullValue
    operationPhaseAngle3Set: float
    def __init__(self, prf: _Optional[_Union[_ProtectionRelayFunction_pb2.ProtectionRelayFunction, _Mapping]] = ..., backwardBlindNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., backwardBlindSet: _Optional[float] = ..., backwardReachNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., backwardReachSet: _Optional[float] = ..., backwardReactanceNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., backwardReactanceSet: _Optional[float] = ..., forwardBlindNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., forwardBlindSet: _Optional[float] = ..., forwardReachNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., forwardReachSet: _Optional[float] = ..., forwardReactanceNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., forwardReactanceSet: _Optional[float] = ..., operationPhaseAngle1Null: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., operationPhaseAngle1Set: _Optional[float] = ..., operationPhaseAngle2Null: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., operationPhaseAngle2Set: _Optional[float] = ..., operationPhaseAngle3Null: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., operationPhaseAngle3Set: _Optional[float] = ...) -> None: ...
