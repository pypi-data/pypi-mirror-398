from zepben.protobuf.cim.iec61970.base.wires import PhaseShuntConnectionKind_pb2 as _PhaseShuntConnectionKind_pb2
from zepben.protobuf.cim.iec61970.base.wires import RegulatingCondEq_pb2 as _RegulatingCondEq_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ShuntCompensator(_message.Message):
    __slots__ = ("rce", "sectionsNull", "sectionsSet", "groundedNull", "groundedSet", "nomUNull", "nomUSet", "phaseConnection")
    RCE_FIELD_NUMBER: _ClassVar[int]
    SECTIONSNULL_FIELD_NUMBER: _ClassVar[int]
    SECTIONSSET_FIELD_NUMBER: _ClassVar[int]
    GROUNDEDNULL_FIELD_NUMBER: _ClassVar[int]
    GROUNDEDSET_FIELD_NUMBER: _ClassVar[int]
    NOMUNULL_FIELD_NUMBER: _ClassVar[int]
    NOMUSET_FIELD_NUMBER: _ClassVar[int]
    PHASECONNECTION_FIELD_NUMBER: _ClassVar[int]
    rce: _RegulatingCondEq_pb2.RegulatingCondEq
    sectionsNull: _struct_pb2.NullValue
    sectionsSet: float
    groundedNull: _struct_pb2.NullValue
    groundedSet: bool
    nomUNull: _struct_pb2.NullValue
    nomUSet: int
    phaseConnection: _PhaseShuntConnectionKind_pb2.PhaseShuntConnectionKind
    def __init__(self, rce: _Optional[_Union[_RegulatingCondEq_pb2.RegulatingCondEq, _Mapping]] = ..., sectionsNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., sectionsSet: _Optional[float] = ..., groundedNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., groundedSet: bool = ..., nomUNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., nomUSet: _Optional[int] = ..., phaseConnection: _Optional[_Union[_PhaseShuntConnectionKind_pb2.PhaseShuntConnectionKind, str]] = ...) -> None: ...
