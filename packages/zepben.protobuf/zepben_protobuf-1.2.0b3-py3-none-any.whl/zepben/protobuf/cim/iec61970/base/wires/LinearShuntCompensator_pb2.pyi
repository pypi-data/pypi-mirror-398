from zepben.protobuf.cim.iec61970.base.wires import ShuntCompensator_pb2 as _ShuntCompensator_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class LinearShuntCompensator(_message.Message):
    __slots__ = ("sc", "b0PerSectionNull", "b0PerSectionSet", "bPerSectionNull", "bPerSectionSet", "g0PerSectionNull", "g0PerSectionSet", "gPerSectionNull", "gPerSectionSet")
    SC_FIELD_NUMBER: _ClassVar[int]
    B0PERSECTIONNULL_FIELD_NUMBER: _ClassVar[int]
    B0PERSECTIONSET_FIELD_NUMBER: _ClassVar[int]
    BPERSECTIONNULL_FIELD_NUMBER: _ClassVar[int]
    BPERSECTIONSET_FIELD_NUMBER: _ClassVar[int]
    G0PERSECTIONNULL_FIELD_NUMBER: _ClassVar[int]
    G0PERSECTIONSET_FIELD_NUMBER: _ClassVar[int]
    GPERSECTIONNULL_FIELD_NUMBER: _ClassVar[int]
    GPERSECTIONSET_FIELD_NUMBER: _ClassVar[int]
    sc: _ShuntCompensator_pb2.ShuntCompensator
    b0PerSectionNull: _struct_pb2.NullValue
    b0PerSectionSet: float
    bPerSectionNull: _struct_pb2.NullValue
    bPerSectionSet: float
    g0PerSectionNull: _struct_pb2.NullValue
    g0PerSectionSet: float
    gPerSectionNull: _struct_pb2.NullValue
    gPerSectionSet: float
    def __init__(self, sc: _Optional[_Union[_ShuntCompensator_pb2.ShuntCompensator, _Mapping]] = ..., b0PerSectionNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., b0PerSectionSet: _Optional[float] = ..., bPerSectionNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., bPerSectionSet: _Optional[float] = ..., g0PerSectionNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., g0PerSectionSet: _Optional[float] = ..., gPerSectionNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., gPerSectionSet: _Optional[float] = ...) -> None: ...
