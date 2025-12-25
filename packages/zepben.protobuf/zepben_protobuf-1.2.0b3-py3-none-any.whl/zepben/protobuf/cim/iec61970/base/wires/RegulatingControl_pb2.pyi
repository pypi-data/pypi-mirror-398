from zepben.protobuf.cim.iec61970.base.core import PhaseCode_pb2 as _PhaseCode_pb2
from zepben.protobuf.cim.iec61970.base.core import PowerSystemResource_pb2 as _PowerSystemResource_pb2
from zepben.protobuf.cim.iec61970.base.wires import RegulatingControlModeKind_pb2 as _RegulatingControlModeKind_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RegulatingControl(_message.Message):
    __slots__ = ("psr", "discreteNull", "discreteSet", "mode", "monitoredPhase", "targetDeadbandNull", "targetDeadbandSet", "targetValueNull", "targetValueSet", "enabledNull", "enabledSet", "maxAllowedTargetValueNull", "maxAllowedTargetValueSet", "minAllowedTargetValueNull", "minAllowedTargetValueSet", "terminalMRID", "regulatingCondEqMRIDs", "ratedCurrentNull", "ratedCurrentSet", "ctPrimaryNull", "ctPrimarySet", "minTargetDeadbandNull", "minTargetDeadbandSet")
    PSR_FIELD_NUMBER: _ClassVar[int]
    DISCRETENULL_FIELD_NUMBER: _ClassVar[int]
    DISCRETESET_FIELD_NUMBER: _ClassVar[int]
    MODE_FIELD_NUMBER: _ClassVar[int]
    MONITOREDPHASE_FIELD_NUMBER: _ClassVar[int]
    TARGETDEADBANDNULL_FIELD_NUMBER: _ClassVar[int]
    TARGETDEADBANDSET_FIELD_NUMBER: _ClassVar[int]
    TARGETVALUENULL_FIELD_NUMBER: _ClassVar[int]
    TARGETVALUESET_FIELD_NUMBER: _ClassVar[int]
    ENABLEDNULL_FIELD_NUMBER: _ClassVar[int]
    ENABLEDSET_FIELD_NUMBER: _ClassVar[int]
    MAXALLOWEDTARGETVALUENULL_FIELD_NUMBER: _ClassVar[int]
    MAXALLOWEDTARGETVALUESET_FIELD_NUMBER: _ClassVar[int]
    MINALLOWEDTARGETVALUENULL_FIELD_NUMBER: _ClassVar[int]
    MINALLOWEDTARGETVALUESET_FIELD_NUMBER: _ClassVar[int]
    TERMINALMRID_FIELD_NUMBER: _ClassVar[int]
    REGULATINGCONDEQMRIDS_FIELD_NUMBER: _ClassVar[int]
    RATEDCURRENTNULL_FIELD_NUMBER: _ClassVar[int]
    RATEDCURRENTSET_FIELD_NUMBER: _ClassVar[int]
    CTPRIMARYNULL_FIELD_NUMBER: _ClassVar[int]
    CTPRIMARYSET_FIELD_NUMBER: _ClassVar[int]
    MINTARGETDEADBANDNULL_FIELD_NUMBER: _ClassVar[int]
    MINTARGETDEADBANDSET_FIELD_NUMBER: _ClassVar[int]
    psr: _PowerSystemResource_pb2.PowerSystemResource
    discreteNull: _struct_pb2.NullValue
    discreteSet: bool
    mode: _RegulatingControlModeKind_pb2.RegulatingControlModeKind
    monitoredPhase: _PhaseCode_pb2.PhaseCode
    targetDeadbandNull: _struct_pb2.NullValue
    targetDeadbandSet: float
    targetValueNull: _struct_pb2.NullValue
    targetValueSet: float
    enabledNull: _struct_pb2.NullValue
    enabledSet: bool
    maxAllowedTargetValueNull: _struct_pb2.NullValue
    maxAllowedTargetValueSet: float
    minAllowedTargetValueNull: _struct_pb2.NullValue
    minAllowedTargetValueSet: float
    terminalMRID: str
    regulatingCondEqMRIDs: _containers.RepeatedScalarFieldContainer[str]
    ratedCurrentNull: _struct_pb2.NullValue
    ratedCurrentSet: float
    ctPrimaryNull: _struct_pb2.NullValue
    ctPrimarySet: float
    minTargetDeadbandNull: _struct_pb2.NullValue
    minTargetDeadbandSet: float
    def __init__(self, psr: _Optional[_Union[_PowerSystemResource_pb2.PowerSystemResource, _Mapping]] = ..., discreteNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., discreteSet: bool = ..., mode: _Optional[_Union[_RegulatingControlModeKind_pb2.RegulatingControlModeKind, str]] = ..., monitoredPhase: _Optional[_Union[_PhaseCode_pb2.PhaseCode, str]] = ..., targetDeadbandNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., targetDeadbandSet: _Optional[float] = ..., targetValueNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., targetValueSet: _Optional[float] = ..., enabledNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., enabledSet: bool = ..., maxAllowedTargetValueNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., maxAllowedTargetValueSet: _Optional[float] = ..., minAllowedTargetValueNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., minAllowedTargetValueSet: _Optional[float] = ..., terminalMRID: _Optional[str] = ..., regulatingCondEqMRIDs: _Optional[_Iterable[str]] = ..., ratedCurrentNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., ratedCurrentSet: _Optional[float] = ..., ctPrimaryNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., ctPrimarySet: _Optional[float] = ..., minTargetDeadbandNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., minTargetDeadbandSet: _Optional[float] = ...) -> None: ...
