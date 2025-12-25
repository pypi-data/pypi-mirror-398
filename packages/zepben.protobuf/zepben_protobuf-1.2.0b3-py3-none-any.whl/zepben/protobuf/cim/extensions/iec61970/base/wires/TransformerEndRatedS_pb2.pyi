from zepben.protobuf.cim.extensions.iec61970.base.wires import TransformerCoolingType_pb2 as _TransformerCoolingType_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class TransformerEndRatedS(_message.Message):
    __slots__ = ("coolingType", "ratedS")
    COOLINGTYPE_FIELD_NUMBER: _ClassVar[int]
    RATEDS_FIELD_NUMBER: _ClassVar[int]
    coolingType: _TransformerCoolingType_pb2.TransformerCoolingType
    ratedS: int
    def __init__(self, coolingType: _Optional[_Union[_TransformerCoolingType_pb2.TransformerCoolingType, str]] = ..., ratedS: _Optional[int] = ...) -> None: ...
