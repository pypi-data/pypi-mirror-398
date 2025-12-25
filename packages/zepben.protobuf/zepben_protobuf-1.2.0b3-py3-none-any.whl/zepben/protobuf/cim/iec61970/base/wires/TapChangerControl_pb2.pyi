from google.protobuf import struct_pb2 as _struct_pb2
from zepben.protobuf.cim.iec61970.base.wires import RegulatingControl_pb2 as _RegulatingControl_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class TapChangerControl(_message.Message):
    __slots__ = ("rc", "limitVoltageNull", "limitVoltageSet", "lineDropCompensationNull", "lineDropCompensationSet", "lineDropRNull", "lineDropRSet", "lineDropXNull", "lineDropXSet", "reverseLineDropRNull", "reverseLineDropRSet", "reverseLineDropXNull", "reverseLineDropXSet", "forwardLDCBlockingNull", "forwardLDCBlockingSet", "timeDelayNull", "timeDelaySet", "coGenerationEnabledNull", "coGenerationEnabledSet")
    RC_FIELD_NUMBER: _ClassVar[int]
    LIMITVOLTAGENULL_FIELD_NUMBER: _ClassVar[int]
    LIMITVOLTAGESET_FIELD_NUMBER: _ClassVar[int]
    LINEDROPCOMPENSATIONNULL_FIELD_NUMBER: _ClassVar[int]
    LINEDROPCOMPENSATIONSET_FIELD_NUMBER: _ClassVar[int]
    LINEDROPRNULL_FIELD_NUMBER: _ClassVar[int]
    LINEDROPRSET_FIELD_NUMBER: _ClassVar[int]
    LINEDROPXNULL_FIELD_NUMBER: _ClassVar[int]
    LINEDROPXSET_FIELD_NUMBER: _ClassVar[int]
    REVERSELINEDROPRNULL_FIELD_NUMBER: _ClassVar[int]
    REVERSELINEDROPRSET_FIELD_NUMBER: _ClassVar[int]
    REVERSELINEDROPXNULL_FIELD_NUMBER: _ClassVar[int]
    REVERSELINEDROPXSET_FIELD_NUMBER: _ClassVar[int]
    FORWARDLDCBLOCKINGNULL_FIELD_NUMBER: _ClassVar[int]
    FORWARDLDCBLOCKINGSET_FIELD_NUMBER: _ClassVar[int]
    TIMEDELAYNULL_FIELD_NUMBER: _ClassVar[int]
    TIMEDELAYSET_FIELD_NUMBER: _ClassVar[int]
    COGENERATIONENABLEDNULL_FIELD_NUMBER: _ClassVar[int]
    COGENERATIONENABLEDSET_FIELD_NUMBER: _ClassVar[int]
    rc: _RegulatingControl_pb2.RegulatingControl
    limitVoltageNull: _struct_pb2.NullValue
    limitVoltageSet: int
    lineDropCompensationNull: _struct_pb2.NullValue
    lineDropCompensationSet: bool
    lineDropRNull: _struct_pb2.NullValue
    lineDropRSet: float
    lineDropXNull: _struct_pb2.NullValue
    lineDropXSet: float
    reverseLineDropRNull: _struct_pb2.NullValue
    reverseLineDropRSet: float
    reverseLineDropXNull: _struct_pb2.NullValue
    reverseLineDropXSet: float
    forwardLDCBlockingNull: _struct_pb2.NullValue
    forwardLDCBlockingSet: bool
    timeDelayNull: _struct_pb2.NullValue
    timeDelaySet: float
    coGenerationEnabledNull: _struct_pb2.NullValue
    coGenerationEnabledSet: bool
    def __init__(self, rc: _Optional[_Union[_RegulatingControl_pb2.RegulatingControl, _Mapping]] = ..., limitVoltageNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., limitVoltageSet: _Optional[int] = ..., lineDropCompensationNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., lineDropCompensationSet: bool = ..., lineDropRNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., lineDropRSet: _Optional[float] = ..., lineDropXNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., lineDropXSet: _Optional[float] = ..., reverseLineDropRNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., reverseLineDropRSet: _Optional[float] = ..., reverseLineDropXNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., reverseLineDropXSet: _Optional[float] = ..., forwardLDCBlockingNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., forwardLDCBlockingSet: bool = ..., timeDelayNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., timeDelaySet: _Optional[float] = ..., coGenerationEnabledNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., coGenerationEnabledSet: bool = ...) -> None: ...
