from zepben.protobuf.cim.iec61970.base.core import PowerSystemResource_pb2 as _PowerSystemResource_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class TapChanger(_message.Message):
    __slots__ = ("psr", "highStepNull", "highStepSet", "lowStepNull", "lowStepSet", "stepNull", "stepSet", "neutralStepNull", "neutralStepSet", "neutralUNull", "neutralUSet", "normalStepNull", "normalStepSet", "controlEnabledNull", "controlEnabledSet", "tapChangerControlMRID")
    PSR_FIELD_NUMBER: _ClassVar[int]
    HIGHSTEPNULL_FIELD_NUMBER: _ClassVar[int]
    HIGHSTEPSET_FIELD_NUMBER: _ClassVar[int]
    LOWSTEPNULL_FIELD_NUMBER: _ClassVar[int]
    LOWSTEPSET_FIELD_NUMBER: _ClassVar[int]
    STEPNULL_FIELD_NUMBER: _ClassVar[int]
    STEPSET_FIELD_NUMBER: _ClassVar[int]
    NEUTRALSTEPNULL_FIELD_NUMBER: _ClassVar[int]
    NEUTRALSTEPSET_FIELD_NUMBER: _ClassVar[int]
    NEUTRALUNULL_FIELD_NUMBER: _ClassVar[int]
    NEUTRALUSET_FIELD_NUMBER: _ClassVar[int]
    NORMALSTEPNULL_FIELD_NUMBER: _ClassVar[int]
    NORMALSTEPSET_FIELD_NUMBER: _ClassVar[int]
    CONTROLENABLEDNULL_FIELD_NUMBER: _ClassVar[int]
    CONTROLENABLEDSET_FIELD_NUMBER: _ClassVar[int]
    TAPCHANGERCONTROLMRID_FIELD_NUMBER: _ClassVar[int]
    psr: _PowerSystemResource_pb2.PowerSystemResource
    highStepNull: _struct_pb2.NullValue
    highStepSet: int
    lowStepNull: _struct_pb2.NullValue
    lowStepSet: int
    stepNull: _struct_pb2.NullValue
    stepSet: float
    neutralStepNull: _struct_pb2.NullValue
    neutralStepSet: int
    neutralUNull: _struct_pb2.NullValue
    neutralUSet: int
    normalStepNull: _struct_pb2.NullValue
    normalStepSet: int
    controlEnabledNull: _struct_pb2.NullValue
    controlEnabledSet: bool
    tapChangerControlMRID: str
    def __init__(self, psr: _Optional[_Union[_PowerSystemResource_pb2.PowerSystemResource, _Mapping]] = ..., highStepNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., highStepSet: _Optional[int] = ..., lowStepNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., lowStepSet: _Optional[int] = ..., stepNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., stepSet: _Optional[float] = ..., neutralStepNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., neutralStepSet: _Optional[int] = ..., neutralUNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., neutralUSet: _Optional[int] = ..., normalStepNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., normalStepSet: _Optional[int] = ..., controlEnabledNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., controlEnabledSet: bool = ..., tapChangerControlMRID: _Optional[str] = ...) -> None: ...
