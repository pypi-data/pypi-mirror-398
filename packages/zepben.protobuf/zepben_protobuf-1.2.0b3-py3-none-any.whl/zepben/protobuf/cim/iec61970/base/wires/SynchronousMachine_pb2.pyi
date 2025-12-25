from zepben.protobuf.cim.iec61970.base.wires import RotatingMachine_pb2 as _RotatingMachine_pb2
from zepben.protobuf.cim.iec61970.base.wires import SynchronousMachineKind_pb2 as _SynchronousMachineKind_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SynchronousMachine(_message.Message):
    __slots__ = ("rm", "baseQNull", "baseQSet", "condenserPNull", "condenserPSet", "earthingNull", "earthingSet", "earthingStarPointRNull", "earthingStarPointRSet", "earthingStarPointXNull", "earthingStarPointXSet", "ikkNull", "ikkSet", "maxQNull", "maxQSet", "maxUNull", "maxUSet", "minQNull", "minQSet", "minUNull", "minUSet", "muNull", "muSet", "rNull", "rSet", "r0Null", "r0Set", "r2Null", "r2Set", "satDirectSubtransXNull", "satDirectSubtransXSet", "satDirectSyncXNull", "satDirectSyncXSet", "satDirectTransXNull", "satDirectTransXSet", "x0Null", "x0Set", "x2Null", "x2Set", "type", "operatingMode", "reactiveCapabilityCurveMRIDs")
    RM_FIELD_NUMBER: _ClassVar[int]
    BASEQNULL_FIELD_NUMBER: _ClassVar[int]
    BASEQSET_FIELD_NUMBER: _ClassVar[int]
    CONDENSERPNULL_FIELD_NUMBER: _ClassVar[int]
    CONDENSERPSET_FIELD_NUMBER: _ClassVar[int]
    EARTHINGNULL_FIELD_NUMBER: _ClassVar[int]
    EARTHINGSET_FIELD_NUMBER: _ClassVar[int]
    EARTHINGSTARPOINTRNULL_FIELD_NUMBER: _ClassVar[int]
    EARTHINGSTARPOINTRSET_FIELD_NUMBER: _ClassVar[int]
    EARTHINGSTARPOINTXNULL_FIELD_NUMBER: _ClassVar[int]
    EARTHINGSTARPOINTXSET_FIELD_NUMBER: _ClassVar[int]
    IKKNULL_FIELD_NUMBER: _ClassVar[int]
    IKKSET_FIELD_NUMBER: _ClassVar[int]
    MAXQNULL_FIELD_NUMBER: _ClassVar[int]
    MAXQSET_FIELD_NUMBER: _ClassVar[int]
    MAXUNULL_FIELD_NUMBER: _ClassVar[int]
    MAXUSET_FIELD_NUMBER: _ClassVar[int]
    MINQNULL_FIELD_NUMBER: _ClassVar[int]
    MINQSET_FIELD_NUMBER: _ClassVar[int]
    MINUNULL_FIELD_NUMBER: _ClassVar[int]
    MINUSET_FIELD_NUMBER: _ClassVar[int]
    MUNULL_FIELD_NUMBER: _ClassVar[int]
    MUSET_FIELD_NUMBER: _ClassVar[int]
    RNULL_FIELD_NUMBER: _ClassVar[int]
    RSET_FIELD_NUMBER: _ClassVar[int]
    R0NULL_FIELD_NUMBER: _ClassVar[int]
    R0SET_FIELD_NUMBER: _ClassVar[int]
    R2NULL_FIELD_NUMBER: _ClassVar[int]
    R2SET_FIELD_NUMBER: _ClassVar[int]
    SATDIRECTSUBTRANSXNULL_FIELD_NUMBER: _ClassVar[int]
    SATDIRECTSUBTRANSXSET_FIELD_NUMBER: _ClassVar[int]
    SATDIRECTSYNCXNULL_FIELD_NUMBER: _ClassVar[int]
    SATDIRECTSYNCXSET_FIELD_NUMBER: _ClassVar[int]
    SATDIRECTTRANSXNULL_FIELD_NUMBER: _ClassVar[int]
    SATDIRECTTRANSXSET_FIELD_NUMBER: _ClassVar[int]
    X0NULL_FIELD_NUMBER: _ClassVar[int]
    X0SET_FIELD_NUMBER: _ClassVar[int]
    X2NULL_FIELD_NUMBER: _ClassVar[int]
    X2SET_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    OPERATINGMODE_FIELD_NUMBER: _ClassVar[int]
    REACTIVECAPABILITYCURVEMRIDS_FIELD_NUMBER: _ClassVar[int]
    rm: _RotatingMachine_pb2.RotatingMachine
    baseQNull: _struct_pb2.NullValue
    baseQSet: float
    condenserPNull: _struct_pb2.NullValue
    condenserPSet: int
    earthingNull: _struct_pb2.NullValue
    earthingSet: bool
    earthingStarPointRNull: _struct_pb2.NullValue
    earthingStarPointRSet: float
    earthingStarPointXNull: _struct_pb2.NullValue
    earthingStarPointXSet: float
    ikkNull: _struct_pb2.NullValue
    ikkSet: float
    maxQNull: _struct_pb2.NullValue
    maxQSet: float
    maxUNull: _struct_pb2.NullValue
    maxUSet: int
    minQNull: _struct_pb2.NullValue
    minQSet: float
    minUNull: _struct_pb2.NullValue
    minUSet: int
    muNull: _struct_pb2.NullValue
    muSet: float
    rNull: _struct_pb2.NullValue
    rSet: float
    r0Null: _struct_pb2.NullValue
    r0Set: float
    r2Null: _struct_pb2.NullValue
    r2Set: float
    satDirectSubtransXNull: _struct_pb2.NullValue
    satDirectSubtransXSet: float
    satDirectSyncXNull: _struct_pb2.NullValue
    satDirectSyncXSet: float
    satDirectTransXNull: _struct_pb2.NullValue
    satDirectTransXSet: float
    x0Null: _struct_pb2.NullValue
    x0Set: float
    x2Null: _struct_pb2.NullValue
    x2Set: float
    type: _SynchronousMachineKind_pb2.SynchronousMachineKind
    operatingMode: _SynchronousMachineKind_pb2.SynchronousMachineKind
    reactiveCapabilityCurveMRIDs: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, rm: _Optional[_Union[_RotatingMachine_pb2.RotatingMachine, _Mapping]] = ..., baseQNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., baseQSet: _Optional[float] = ..., condenserPNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., condenserPSet: _Optional[int] = ..., earthingNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., earthingSet: bool = ..., earthingStarPointRNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., earthingStarPointRSet: _Optional[float] = ..., earthingStarPointXNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., earthingStarPointXSet: _Optional[float] = ..., ikkNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., ikkSet: _Optional[float] = ..., maxQNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., maxQSet: _Optional[float] = ..., maxUNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., maxUSet: _Optional[int] = ..., minQNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., minQSet: _Optional[float] = ..., minUNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., minUSet: _Optional[int] = ..., muNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., muSet: _Optional[float] = ..., rNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., rSet: _Optional[float] = ..., r0Null: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., r0Set: _Optional[float] = ..., r2Null: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., r2Set: _Optional[float] = ..., satDirectSubtransXNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., satDirectSubtransXSet: _Optional[float] = ..., satDirectSyncXNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., satDirectSyncXSet: _Optional[float] = ..., satDirectTransXNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., satDirectTransXSet: _Optional[float] = ..., x0Null: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., x0Set: _Optional[float] = ..., x2Null: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., x2Set: _Optional[float] = ..., type: _Optional[_Union[_SynchronousMachineKind_pb2.SynchronousMachineKind, str]] = ..., operatingMode: _Optional[_Union[_SynchronousMachineKind_pb2.SynchronousMachineKind, str]] = ..., reactiveCapabilityCurveMRIDs: _Optional[_Iterable[str]] = ...) -> None: ...
