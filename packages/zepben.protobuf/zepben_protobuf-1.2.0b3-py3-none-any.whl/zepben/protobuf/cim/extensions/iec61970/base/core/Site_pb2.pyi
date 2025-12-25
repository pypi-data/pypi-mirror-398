from zepben.protobuf.cim.iec61970.base.core import EquipmentContainer_pb2 as _EquipmentContainer_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Site(_message.Message):
    __slots__ = ("ec",)
    EC_FIELD_NUMBER: _ClassVar[int]
    ec: _EquipmentContainer_pb2.EquipmentContainer
    def __init__(self, ec: _Optional[_Union[_EquipmentContainer_pb2.EquipmentContainer, _Mapping]] = ...) -> None: ...
