from zepben.protobuf.cim.iec61970.base.generation.production import PowerElectronicsUnit_pb2 as _PowerElectronicsUnit_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class EvChargingUnit(_message.Message):
    __slots__ = ("peu",)
    PEU_FIELD_NUMBER: _ClassVar[int]
    peu: _PowerElectronicsUnit_pb2.PowerElectronicsUnit
    def __init__(self, peu: _Optional[_Union[_PowerElectronicsUnit_pb2.PowerElectronicsUnit, _Mapping]] = ...) -> None: ...
