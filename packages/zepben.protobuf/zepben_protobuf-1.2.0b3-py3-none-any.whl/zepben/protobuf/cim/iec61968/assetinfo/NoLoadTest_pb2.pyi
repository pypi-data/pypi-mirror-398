from zepben.protobuf.cim.iec61968.assetinfo import TransformerTest_pb2 as _TransformerTest_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class NoLoadTest(_message.Message):
    __slots__ = ("tt", "energisedEndVoltageNull", "energisedEndVoltageSet", "excitingCurrentNull", "excitingCurrentSet", "excitingCurrentZeroNull", "excitingCurrentZeroSet", "lossNull", "lossSet", "lossZeroNull", "lossZeroSet")
    TT_FIELD_NUMBER: _ClassVar[int]
    ENERGISEDENDVOLTAGENULL_FIELD_NUMBER: _ClassVar[int]
    ENERGISEDENDVOLTAGESET_FIELD_NUMBER: _ClassVar[int]
    EXCITINGCURRENTNULL_FIELD_NUMBER: _ClassVar[int]
    EXCITINGCURRENTSET_FIELD_NUMBER: _ClassVar[int]
    EXCITINGCURRENTZERONULL_FIELD_NUMBER: _ClassVar[int]
    EXCITINGCURRENTZEROSET_FIELD_NUMBER: _ClassVar[int]
    LOSSNULL_FIELD_NUMBER: _ClassVar[int]
    LOSSSET_FIELD_NUMBER: _ClassVar[int]
    LOSSZERONULL_FIELD_NUMBER: _ClassVar[int]
    LOSSZEROSET_FIELD_NUMBER: _ClassVar[int]
    tt: _TransformerTest_pb2.TransformerTest
    energisedEndVoltageNull: _struct_pb2.NullValue
    energisedEndVoltageSet: int
    excitingCurrentNull: _struct_pb2.NullValue
    excitingCurrentSet: float
    excitingCurrentZeroNull: _struct_pb2.NullValue
    excitingCurrentZeroSet: float
    lossNull: _struct_pb2.NullValue
    lossSet: int
    lossZeroNull: _struct_pb2.NullValue
    lossZeroSet: int
    def __init__(self, tt: _Optional[_Union[_TransformerTest_pb2.TransformerTest, _Mapping]] = ..., energisedEndVoltageNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., energisedEndVoltageSet: _Optional[int] = ..., excitingCurrentNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., excitingCurrentSet: _Optional[float] = ..., excitingCurrentZeroNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., excitingCurrentZeroSet: _Optional[float] = ..., lossNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., lossSet: _Optional[int] = ..., lossZeroNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., lossZeroSet: _Optional[int] = ...) -> None: ...
