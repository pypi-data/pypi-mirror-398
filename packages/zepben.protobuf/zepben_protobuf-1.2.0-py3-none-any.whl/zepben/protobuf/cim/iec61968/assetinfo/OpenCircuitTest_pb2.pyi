from zepben.protobuf.cim.iec61968.assetinfo import TransformerTest_pb2 as _TransformerTest_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class OpenCircuitTest(_message.Message):
    __slots__ = ("tt", "energisedEndStepNull", "energisedEndStepSet", "energisedEndVoltageNull", "energisedEndVoltageSet", "openEndStepNull", "openEndStepSet", "openEndVoltageNull", "openEndVoltageSet", "phaseShiftNull", "phaseShiftSet")
    TT_FIELD_NUMBER: _ClassVar[int]
    ENERGISEDENDSTEPNULL_FIELD_NUMBER: _ClassVar[int]
    ENERGISEDENDSTEPSET_FIELD_NUMBER: _ClassVar[int]
    ENERGISEDENDVOLTAGENULL_FIELD_NUMBER: _ClassVar[int]
    ENERGISEDENDVOLTAGESET_FIELD_NUMBER: _ClassVar[int]
    OPENENDSTEPNULL_FIELD_NUMBER: _ClassVar[int]
    OPENENDSTEPSET_FIELD_NUMBER: _ClassVar[int]
    OPENENDVOLTAGENULL_FIELD_NUMBER: _ClassVar[int]
    OPENENDVOLTAGESET_FIELD_NUMBER: _ClassVar[int]
    PHASESHIFTNULL_FIELD_NUMBER: _ClassVar[int]
    PHASESHIFTSET_FIELD_NUMBER: _ClassVar[int]
    tt: _TransformerTest_pb2.TransformerTest
    energisedEndStepNull: _struct_pb2.NullValue
    energisedEndStepSet: int
    energisedEndVoltageNull: _struct_pb2.NullValue
    energisedEndVoltageSet: int
    openEndStepNull: _struct_pb2.NullValue
    openEndStepSet: int
    openEndVoltageNull: _struct_pb2.NullValue
    openEndVoltageSet: int
    phaseShiftNull: _struct_pb2.NullValue
    phaseShiftSet: float
    def __init__(self, tt: _Optional[_Union[_TransformerTest_pb2.TransformerTest, _Mapping]] = ..., energisedEndStepNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., energisedEndStepSet: _Optional[int] = ..., energisedEndVoltageNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., energisedEndVoltageSet: _Optional[int] = ..., openEndStepNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., openEndStepSet: _Optional[int] = ..., openEndVoltageNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., openEndVoltageSet: _Optional[int] = ..., phaseShiftNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., phaseShiftSet: _Optional[float] = ...) -> None: ...
