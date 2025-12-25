from zepben.protobuf.cim.iec61970.base.wires import EarthFaultCompensator_pb2 as _EarthFaultCompensator_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PetersenCoil(_message.Message):
    __slots__ = ("efc", "xGroundNominalNull", "xGroundNominalSet")
    EFC_FIELD_NUMBER: _ClassVar[int]
    XGROUNDNOMINALNULL_FIELD_NUMBER: _ClassVar[int]
    XGROUNDNOMINALSET_FIELD_NUMBER: _ClassVar[int]
    efc: _EarthFaultCompensator_pb2.EarthFaultCompensator
    xGroundNominalNull: _struct_pb2.NullValue
    xGroundNominalSet: float
    def __init__(self, efc: _Optional[_Union[_EarthFaultCompensator_pb2.EarthFaultCompensator, _Mapping]] = ..., xGroundNominalNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., xGroundNominalSet: _Optional[float] = ...) -> None: ...
