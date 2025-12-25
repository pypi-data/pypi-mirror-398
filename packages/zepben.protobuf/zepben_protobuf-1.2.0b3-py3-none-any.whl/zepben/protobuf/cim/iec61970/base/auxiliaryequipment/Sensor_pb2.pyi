from zepben.protobuf.cim.iec61970.base.auxiliaryequipment import AuxiliaryEquipment_pb2 as _AuxiliaryEquipment_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Sensor(_message.Message):
    __slots__ = ("ae", "relayFunctionMRIDs")
    AE_FIELD_NUMBER: _ClassVar[int]
    RELAYFUNCTIONMRIDS_FIELD_NUMBER: _ClassVar[int]
    ae: _AuxiliaryEquipment_pb2.AuxiliaryEquipment
    relayFunctionMRIDs: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, ae: _Optional[_Union[_AuxiliaryEquipment_pb2.AuxiliaryEquipment, _Mapping]] = ..., relayFunctionMRIDs: _Optional[_Iterable[str]] = ...) -> None: ...
