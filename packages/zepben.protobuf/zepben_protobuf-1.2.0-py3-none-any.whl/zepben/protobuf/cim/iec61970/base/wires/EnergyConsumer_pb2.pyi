from zepben.protobuf.cim.iec61970.base.wires import EnergyConnection_pb2 as _EnergyConnection_pb2
from zepben.protobuf.cim.iec61970.base.wires import PhaseShuntConnectionKind_pb2 as _PhaseShuntConnectionKind_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class EnergyConsumer(_message.Message):
    __slots__ = ("ec", "energyConsumerPhasesMRIDs", "customerCountNull", "customerCountSet", "groundedNull", "groundedSet", "pNull", "pSet", "pFixedNull", "pFixedSet", "phaseConnection", "qNull", "qSet", "qFixedNull", "qFixedSet")
    EC_FIELD_NUMBER: _ClassVar[int]
    ENERGYCONSUMERPHASESMRIDS_FIELD_NUMBER: _ClassVar[int]
    CUSTOMERCOUNTNULL_FIELD_NUMBER: _ClassVar[int]
    CUSTOMERCOUNTSET_FIELD_NUMBER: _ClassVar[int]
    GROUNDEDNULL_FIELD_NUMBER: _ClassVar[int]
    GROUNDEDSET_FIELD_NUMBER: _ClassVar[int]
    PNULL_FIELD_NUMBER: _ClassVar[int]
    PSET_FIELD_NUMBER: _ClassVar[int]
    PFIXEDNULL_FIELD_NUMBER: _ClassVar[int]
    PFIXEDSET_FIELD_NUMBER: _ClassVar[int]
    PHASECONNECTION_FIELD_NUMBER: _ClassVar[int]
    QNULL_FIELD_NUMBER: _ClassVar[int]
    QSET_FIELD_NUMBER: _ClassVar[int]
    QFIXEDNULL_FIELD_NUMBER: _ClassVar[int]
    QFIXEDSET_FIELD_NUMBER: _ClassVar[int]
    ec: _EnergyConnection_pb2.EnergyConnection
    energyConsumerPhasesMRIDs: _containers.RepeatedScalarFieldContainer[str]
    customerCountNull: _struct_pb2.NullValue
    customerCountSet: int
    groundedNull: _struct_pb2.NullValue
    groundedSet: bool
    pNull: _struct_pb2.NullValue
    pSet: float
    pFixedNull: _struct_pb2.NullValue
    pFixedSet: float
    phaseConnection: _PhaseShuntConnectionKind_pb2.PhaseShuntConnectionKind
    qNull: _struct_pb2.NullValue
    qSet: float
    qFixedNull: _struct_pb2.NullValue
    qFixedSet: float
    def __init__(self, ec: _Optional[_Union[_EnergyConnection_pb2.EnergyConnection, _Mapping]] = ..., energyConsumerPhasesMRIDs: _Optional[_Iterable[str]] = ..., customerCountNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., customerCountSet: _Optional[int] = ..., groundedNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., groundedSet: bool = ..., pNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., pSet: _Optional[float] = ..., pFixedNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., pFixedSet: _Optional[float] = ..., phaseConnection: _Optional[_Union[_PhaseShuntConnectionKind_pb2.PhaseShuntConnectionKind, str]] = ..., qNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., qSet: _Optional[float] = ..., qFixedNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., qFixedSet: _Optional[float] = ...) -> None: ...
