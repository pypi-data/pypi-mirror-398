from zepben.protobuf.cim.iec61970.base.auxiliaryequipment import AuxiliaryEquipment_pb2 as _AuxiliaryEquipment_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class FaultIndicator(_message.Message):
    __slots__ = ("ae",)
    AE_FIELD_NUMBER: _ClassVar[int]
    ae: _AuxiliaryEquipment_pb2.AuxiliaryEquipment
    def __init__(self, ae: _Optional[_Union[_AuxiliaryEquipment_pb2.AuxiliaryEquipment, _Mapping]] = ...) -> None: ...
