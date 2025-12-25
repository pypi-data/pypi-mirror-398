from zepben.protobuf.cim.iec61970.base.meas import AccumulatorValue_pb2 as _AccumulatorValue_pb2
from zepben.protobuf.cim.iec61970.base.meas import AnalogValue_pb2 as _AnalogValue_pb2
from zepben.protobuf.cim.iec61970.base.meas import DiscreteValue_pb2 as _DiscreteValue_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CreateAnalogValueResponse(_message.Message):
    __slots__ = ("messageId",)
    MESSAGEID_FIELD_NUMBER: _ClassVar[int]
    messageId: int
    def __init__(self, messageId: _Optional[int] = ...) -> None: ...

class CreateAccumulatorValueResponse(_message.Message):
    __slots__ = ("messageId",)
    MESSAGEID_FIELD_NUMBER: _ClassVar[int]
    messageId: int
    def __init__(self, messageId: _Optional[int] = ...) -> None: ...

class CreateDiscreteValueResponse(_message.Message):
    __slots__ = ("messageId",)
    MESSAGEID_FIELD_NUMBER: _ClassVar[int]
    messageId: int
    def __init__(self, messageId: _Optional[int] = ...) -> None: ...

class CreateAnalogValuesResponse(_message.Message):
    __slots__ = ("messageId",)
    MESSAGEID_FIELD_NUMBER: _ClassVar[int]
    messageId: int
    def __init__(self, messageId: _Optional[int] = ...) -> None: ...

class CreateAccumulatorValuesResponse(_message.Message):
    __slots__ = ("messageId",)
    MESSAGEID_FIELD_NUMBER: _ClassVar[int]
    messageId: int
    def __init__(self, messageId: _Optional[int] = ...) -> None: ...

class CreateDiscreteValuesResponse(_message.Message):
    __slots__ = ("messageId",)
    MESSAGEID_FIELD_NUMBER: _ClassVar[int]
    messageId: int
    def __init__(self, messageId: _Optional[int] = ...) -> None: ...

class ErrorDetail(_message.Message):
    __slots__ = ("accumulatorValue", "analogValue", "discreteValue", "error")
    ACCUMULATORVALUE_FIELD_NUMBER: _ClassVar[int]
    ANALOGVALUE_FIELD_NUMBER: _ClassVar[int]
    DISCRETEVALUE_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    accumulatorValue: _AccumulatorValue_pb2.AccumulatorValue
    analogValue: _AnalogValue_pb2.AnalogValue
    discreteValue: _DiscreteValue_pb2.DiscreteValue
    error: str
    def __init__(self, accumulatorValue: _Optional[_Union[_AccumulatorValue_pb2.AccumulatorValue, _Mapping]] = ..., analogValue: _Optional[_Union[_AnalogValue_pb2.AnalogValue, _Mapping]] = ..., discreteValue: _Optional[_Union[_DiscreteValue_pb2.DiscreteValue, _Mapping]] = ..., error: _Optional[str] = ...) -> None: ...

class CreateMeasurementValuesResponse(_message.Message):
    __slots__ = ("messageId", "failed", "errors")
    MESSAGEID_FIELD_NUMBER: _ClassVar[int]
    FAILED_FIELD_NUMBER: _ClassVar[int]
    ERRORS_FIELD_NUMBER: _ClassVar[int]
    messageId: int
    failed: bool
    errors: _containers.RepeatedCompositeFieldContainer[ErrorDetail]
    def __init__(self, messageId: _Optional[int] = ..., failed: bool = ..., errors: _Optional[_Iterable[_Union[ErrorDetail, _Mapping]]] = ...) -> None: ...
