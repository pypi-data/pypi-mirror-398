from zepben.protobuf.cim.iec61970.base.meas import AccumulatorValue_pb2 as _AccumulatorValue_pb2
from zepben.protobuf.cim.iec61970.base.meas import AnalogValue_pb2 as _AnalogValue_pb2
from zepben.protobuf.cim.iec61970.base.meas import DiscreteValue_pb2 as _DiscreteValue_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GetAccumulatorValueResponse(_message.Message):
    __slots__ = ("messageId", "accumulatorValue")
    MESSAGEID_FIELD_NUMBER: _ClassVar[int]
    ACCUMULATORVALUE_FIELD_NUMBER: _ClassVar[int]
    messageId: int
    accumulatorValue: _AccumulatorValue_pb2.AccumulatorValue
    def __init__(self, messageId: _Optional[int] = ..., accumulatorValue: _Optional[_Union[_AccumulatorValue_pb2.AccumulatorValue, _Mapping]] = ...) -> None: ...

class GetAnalogValueResponse(_message.Message):
    __slots__ = ("messageId", "analogValue")
    MESSAGEID_FIELD_NUMBER: _ClassVar[int]
    ANALOGVALUE_FIELD_NUMBER: _ClassVar[int]
    messageId: int
    analogValue: _AnalogValue_pb2.AnalogValue
    def __init__(self, messageId: _Optional[int] = ..., analogValue: _Optional[_Union[_AnalogValue_pb2.AnalogValue, _Mapping]] = ...) -> None: ...

class GetDiscreteValueResponse(_message.Message):
    __slots__ = ("messageId", "discreteValue")
    MESSAGEID_FIELD_NUMBER: _ClassVar[int]
    DISCRETEVALUE_FIELD_NUMBER: _ClassVar[int]
    messageId: int
    discreteValue: _DiscreteValue_pb2.DiscreteValue
    def __init__(self, messageId: _Optional[int] = ..., discreteValue: _Optional[_Union[_DiscreteValue_pb2.DiscreteValue, _Mapping]] = ...) -> None: ...
