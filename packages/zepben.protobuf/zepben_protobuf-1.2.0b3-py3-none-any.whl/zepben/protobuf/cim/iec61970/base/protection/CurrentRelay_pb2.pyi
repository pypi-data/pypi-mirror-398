from zepben.protobuf.cim.extensions.iec61970.base.protection import ProtectionRelayFunction_pb2 as _ProtectionRelayFunction_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CurrentRelay(_message.Message):
    __slots__ = ("prf", "currentLimit1Null", "currentLimit1Set", "inverseTimeFlagNull", "inverseTimeFlagSet", "timeDelay1Null", "timeDelay1Set")
    PRF_FIELD_NUMBER: _ClassVar[int]
    CURRENTLIMIT1NULL_FIELD_NUMBER: _ClassVar[int]
    CURRENTLIMIT1SET_FIELD_NUMBER: _ClassVar[int]
    INVERSETIMEFLAGNULL_FIELD_NUMBER: _ClassVar[int]
    INVERSETIMEFLAGSET_FIELD_NUMBER: _ClassVar[int]
    TIMEDELAY1NULL_FIELD_NUMBER: _ClassVar[int]
    TIMEDELAY1SET_FIELD_NUMBER: _ClassVar[int]
    prf: _ProtectionRelayFunction_pb2.ProtectionRelayFunction
    currentLimit1Null: _struct_pb2.NullValue
    currentLimit1Set: float
    inverseTimeFlagNull: _struct_pb2.NullValue
    inverseTimeFlagSet: bool
    timeDelay1Null: _struct_pb2.NullValue
    timeDelay1Set: float
    def __init__(self, prf: _Optional[_Union[_ProtectionRelayFunction_pb2.ProtectionRelayFunction, _Mapping]] = ..., currentLimit1Null: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., currentLimit1Set: _Optional[float] = ..., inverseTimeFlagNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., inverseTimeFlagSet: bool = ..., timeDelay1Null: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., timeDelay1Set: _Optional[float] = ...) -> None: ...
