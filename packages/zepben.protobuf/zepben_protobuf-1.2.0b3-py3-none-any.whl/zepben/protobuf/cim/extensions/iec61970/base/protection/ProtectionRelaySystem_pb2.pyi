from zepben.protobuf.cim.extensions.iec61970.base.protection import ProtectionKind_pb2 as _ProtectionKind_pb2
from zepben.protobuf.cim.iec61970.base.core import Equipment_pb2 as _Equipment_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ProtectionRelaySystem(_message.Message):
    __slots__ = ("eq", "protectionKind", "schemeMRIDs")
    EQ_FIELD_NUMBER: _ClassVar[int]
    PROTECTIONKIND_FIELD_NUMBER: _ClassVar[int]
    SCHEMEMRIDS_FIELD_NUMBER: _ClassVar[int]
    eq: _Equipment_pb2.Equipment
    protectionKind: _ProtectionKind_pb2.ProtectionKind
    schemeMRIDs: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, eq: _Optional[_Union[_Equipment_pb2.Equipment, _Mapping]] = ..., protectionKind: _Optional[_Union[_ProtectionKind_pb2.ProtectionKind, str]] = ..., schemeMRIDs: _Optional[_Iterable[str]] = ...) -> None: ...
