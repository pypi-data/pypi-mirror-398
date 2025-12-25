from zepben.protobuf.cim.iec61968.assets import AssetInfo_pb2 as _AssetInfo_pb2
from zepben.protobuf.cim.iec61970.base.wires import WindingConnection_pb2 as _WindingConnection_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class TransformerEndInfo(_message.Message):
    __slots__ = ("ai", "connectionKind", "emergencySNull", "emergencySSet", "endNumber", "insulationUNull", "insulationUSet", "phaseAngleClockNull", "phaseAngleClockSet", "rNull", "rSet", "ratedSNull", "ratedSSet", "ratedUNull", "ratedUSet", "shortTermSNull", "shortTermSSet", "transformerTankInfoMRID", "transformerStarImpedanceMRID", "energisedEndNoLoadTestsMRID", "energisedEndShortCircuitTestsMRID", "groundedEndShortCircuitTestsMRID", "openEndOpenCircuitTestsMRID", "energisedEndOpenCircuitTestsMRID")
    AI_FIELD_NUMBER: _ClassVar[int]
    CONNECTIONKIND_FIELD_NUMBER: _ClassVar[int]
    EMERGENCYSNULL_FIELD_NUMBER: _ClassVar[int]
    EMERGENCYSSET_FIELD_NUMBER: _ClassVar[int]
    ENDNUMBER_FIELD_NUMBER: _ClassVar[int]
    INSULATIONUNULL_FIELD_NUMBER: _ClassVar[int]
    INSULATIONUSET_FIELD_NUMBER: _ClassVar[int]
    PHASEANGLECLOCKNULL_FIELD_NUMBER: _ClassVar[int]
    PHASEANGLECLOCKSET_FIELD_NUMBER: _ClassVar[int]
    RNULL_FIELD_NUMBER: _ClassVar[int]
    RSET_FIELD_NUMBER: _ClassVar[int]
    RATEDSNULL_FIELD_NUMBER: _ClassVar[int]
    RATEDSSET_FIELD_NUMBER: _ClassVar[int]
    RATEDUNULL_FIELD_NUMBER: _ClassVar[int]
    RATEDUSET_FIELD_NUMBER: _ClassVar[int]
    SHORTTERMSNULL_FIELD_NUMBER: _ClassVar[int]
    SHORTTERMSSET_FIELD_NUMBER: _ClassVar[int]
    TRANSFORMERTANKINFOMRID_FIELD_NUMBER: _ClassVar[int]
    TRANSFORMERSTARIMPEDANCEMRID_FIELD_NUMBER: _ClassVar[int]
    ENERGISEDENDNOLOADTESTSMRID_FIELD_NUMBER: _ClassVar[int]
    ENERGISEDENDSHORTCIRCUITTESTSMRID_FIELD_NUMBER: _ClassVar[int]
    GROUNDEDENDSHORTCIRCUITTESTSMRID_FIELD_NUMBER: _ClassVar[int]
    OPENENDOPENCIRCUITTESTSMRID_FIELD_NUMBER: _ClassVar[int]
    ENERGISEDENDOPENCIRCUITTESTSMRID_FIELD_NUMBER: _ClassVar[int]
    ai: _AssetInfo_pb2.AssetInfo
    connectionKind: _WindingConnection_pb2.WindingConnection
    emergencySNull: _struct_pb2.NullValue
    emergencySSet: int
    endNumber: int
    insulationUNull: _struct_pb2.NullValue
    insulationUSet: int
    phaseAngleClockNull: _struct_pb2.NullValue
    phaseAngleClockSet: int
    rNull: _struct_pb2.NullValue
    rSet: float
    ratedSNull: _struct_pb2.NullValue
    ratedSSet: int
    ratedUNull: _struct_pb2.NullValue
    ratedUSet: int
    shortTermSNull: _struct_pb2.NullValue
    shortTermSSet: int
    transformerTankInfoMRID: str
    transformerStarImpedanceMRID: str
    energisedEndNoLoadTestsMRID: str
    energisedEndShortCircuitTestsMRID: str
    groundedEndShortCircuitTestsMRID: str
    openEndOpenCircuitTestsMRID: str
    energisedEndOpenCircuitTestsMRID: str
    def __init__(self, ai: _Optional[_Union[_AssetInfo_pb2.AssetInfo, _Mapping]] = ..., connectionKind: _Optional[_Union[_WindingConnection_pb2.WindingConnection, str]] = ..., emergencySNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., emergencySSet: _Optional[int] = ..., endNumber: _Optional[int] = ..., insulationUNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., insulationUSet: _Optional[int] = ..., phaseAngleClockNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., phaseAngleClockSet: _Optional[int] = ..., rNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., rSet: _Optional[float] = ..., ratedSNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., ratedSSet: _Optional[int] = ..., ratedUNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., ratedUSet: _Optional[int] = ..., shortTermSNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., shortTermSSet: _Optional[int] = ..., transformerTankInfoMRID: _Optional[str] = ..., transformerStarImpedanceMRID: _Optional[str] = ..., energisedEndNoLoadTestsMRID: _Optional[str] = ..., energisedEndShortCircuitTestsMRID: _Optional[str] = ..., groundedEndShortCircuitTestsMRID: _Optional[str] = ..., openEndOpenCircuitTestsMRID: _Optional[str] = ..., energisedEndOpenCircuitTestsMRID: _Optional[str] = ...) -> None: ...
