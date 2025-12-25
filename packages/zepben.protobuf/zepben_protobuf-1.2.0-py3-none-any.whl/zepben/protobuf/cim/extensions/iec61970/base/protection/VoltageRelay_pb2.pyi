from zepben.protobuf.cim.extensions.iec61970.base.protection import ProtectionRelayFunction_pb2 as _ProtectionRelayFunction_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class VoltageRelay(_message.Message):
    __slots__ = ("prf",)
    PRF_FIELD_NUMBER: _ClassVar[int]
    prf: _ProtectionRelayFunction_pb2.ProtectionRelayFunction
    def __init__(self, prf: _Optional[_Union[_ProtectionRelayFunction_pb2.ProtectionRelayFunction, _Mapping]] = ...) -> None: ...
