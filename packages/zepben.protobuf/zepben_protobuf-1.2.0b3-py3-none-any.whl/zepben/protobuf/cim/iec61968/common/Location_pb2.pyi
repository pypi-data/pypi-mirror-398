from zepben.protobuf.cim.iec61968.common import PositionPoint_pb2 as _PositionPoint_pb2
from zepben.protobuf.cim.iec61968.common import StreetAddress_pb2 as _StreetAddress_pb2
from zepben.protobuf.cim.iec61970.base.core import IdentifiedObject_pb2 as _IdentifiedObject_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Location(_message.Message):
    __slots__ = ("io", "mainAddress", "positionPoints")
    IO_FIELD_NUMBER: _ClassVar[int]
    MAINADDRESS_FIELD_NUMBER: _ClassVar[int]
    POSITIONPOINTS_FIELD_NUMBER: _ClassVar[int]
    io: _IdentifiedObject_pb2.IdentifiedObject
    mainAddress: _StreetAddress_pb2.StreetAddress
    positionPoints: _containers.RepeatedCompositeFieldContainer[_PositionPoint_pb2.PositionPoint]
    def __init__(self, io: _Optional[_Union[_IdentifiedObject_pb2.IdentifiedObject, _Mapping]] = ..., mainAddress: _Optional[_Union[_StreetAddress_pb2.StreetAddress, _Mapping]] = ..., positionPoints: _Optional[_Iterable[_Union[_PositionPoint_pb2.PositionPoint, _Mapping]]] = ...) -> None: ...
