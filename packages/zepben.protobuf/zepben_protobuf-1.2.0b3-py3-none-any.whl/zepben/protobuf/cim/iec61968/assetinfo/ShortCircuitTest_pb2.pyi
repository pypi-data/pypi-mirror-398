from zepben.protobuf.cim.iec61968.assetinfo import TransformerTest_pb2 as _TransformerTest_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ShortCircuitTest(_message.Message):
    __slots__ = ("tt", "currentNull", "currentSet", "energisedEndStepNull", "energisedEndStepSet", "groundedEndStepNull", "groundedEndStepSet", "leakageImpedanceNull", "leakageImpedanceSet", "leakageImpedanceZeroNull", "leakageImpedanceZeroSet", "lossNull", "lossSet", "lossZeroNull", "lossZeroSet", "powerNull", "powerSet", "voltageNull", "voltageSet", "voltageOhmicPartNull", "voltageOhmicPartSet")
    TT_FIELD_NUMBER: _ClassVar[int]
    CURRENTNULL_FIELD_NUMBER: _ClassVar[int]
    CURRENTSET_FIELD_NUMBER: _ClassVar[int]
    ENERGISEDENDSTEPNULL_FIELD_NUMBER: _ClassVar[int]
    ENERGISEDENDSTEPSET_FIELD_NUMBER: _ClassVar[int]
    GROUNDEDENDSTEPNULL_FIELD_NUMBER: _ClassVar[int]
    GROUNDEDENDSTEPSET_FIELD_NUMBER: _ClassVar[int]
    LEAKAGEIMPEDANCENULL_FIELD_NUMBER: _ClassVar[int]
    LEAKAGEIMPEDANCESET_FIELD_NUMBER: _ClassVar[int]
    LEAKAGEIMPEDANCEZERONULL_FIELD_NUMBER: _ClassVar[int]
    LEAKAGEIMPEDANCEZEROSET_FIELD_NUMBER: _ClassVar[int]
    LOSSNULL_FIELD_NUMBER: _ClassVar[int]
    LOSSSET_FIELD_NUMBER: _ClassVar[int]
    LOSSZERONULL_FIELD_NUMBER: _ClassVar[int]
    LOSSZEROSET_FIELD_NUMBER: _ClassVar[int]
    POWERNULL_FIELD_NUMBER: _ClassVar[int]
    POWERSET_FIELD_NUMBER: _ClassVar[int]
    VOLTAGENULL_FIELD_NUMBER: _ClassVar[int]
    VOLTAGESET_FIELD_NUMBER: _ClassVar[int]
    VOLTAGEOHMICPARTNULL_FIELD_NUMBER: _ClassVar[int]
    VOLTAGEOHMICPARTSET_FIELD_NUMBER: _ClassVar[int]
    tt: _TransformerTest_pb2.TransformerTest
    currentNull: _struct_pb2.NullValue
    currentSet: float
    energisedEndStepNull: _struct_pb2.NullValue
    energisedEndStepSet: int
    groundedEndStepNull: _struct_pb2.NullValue
    groundedEndStepSet: int
    leakageImpedanceNull: _struct_pb2.NullValue
    leakageImpedanceSet: float
    leakageImpedanceZeroNull: _struct_pb2.NullValue
    leakageImpedanceZeroSet: float
    lossNull: _struct_pb2.NullValue
    lossSet: int
    lossZeroNull: _struct_pb2.NullValue
    lossZeroSet: int
    powerNull: _struct_pb2.NullValue
    powerSet: int
    voltageNull: _struct_pb2.NullValue
    voltageSet: float
    voltageOhmicPartNull: _struct_pb2.NullValue
    voltageOhmicPartSet: float
    def __init__(self, tt: _Optional[_Union[_TransformerTest_pb2.TransformerTest, _Mapping]] = ..., currentNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., currentSet: _Optional[float] = ..., energisedEndStepNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., energisedEndStepSet: _Optional[int] = ..., groundedEndStepNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., groundedEndStepSet: _Optional[int] = ..., leakageImpedanceNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., leakageImpedanceSet: _Optional[float] = ..., leakageImpedanceZeroNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., leakageImpedanceZeroSet: _Optional[float] = ..., lossNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., lossSet: _Optional[int] = ..., lossZeroNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., lossZeroSet: _Optional[int] = ..., powerNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., powerSet: _Optional[int] = ..., voltageNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., voltageSet: _Optional[float] = ..., voltageOhmicPartNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., voltageOhmicPartSet: _Optional[float] = ...) -> None: ...
