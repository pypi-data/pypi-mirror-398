from zepben.protobuf.cim.iec61970.base.equivalents import EquivalentEquipment_pb2 as _EquivalentEquipment_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class EquivalentBranch(_message.Message):
    __slots__ = ("ee", "negativeR12Null", "negativeR12Set", "negativeR21Null", "negativeR21Set", "negativeX12Null", "negativeX12Set", "negativeX21Null", "negativeX21Set", "positiveR12Null", "positiveR12Set", "positiveR21Null", "positiveR21Set", "positiveX12Null", "positiveX12Set", "positiveX21Null", "positiveX21Set", "rNull", "rSet", "r21Null", "r21Set", "xNull", "xSet", "x21Null", "x21Set", "zeroR12Null", "zeroR12Set", "zeroR21Null", "zeroR21Set", "zeroX12Null", "zeroX12Set", "zeroX21Null", "zeroX21Set")
    EE_FIELD_NUMBER: _ClassVar[int]
    NEGATIVER12NULL_FIELD_NUMBER: _ClassVar[int]
    NEGATIVER12SET_FIELD_NUMBER: _ClassVar[int]
    NEGATIVER21NULL_FIELD_NUMBER: _ClassVar[int]
    NEGATIVER21SET_FIELD_NUMBER: _ClassVar[int]
    NEGATIVEX12NULL_FIELD_NUMBER: _ClassVar[int]
    NEGATIVEX12SET_FIELD_NUMBER: _ClassVar[int]
    NEGATIVEX21NULL_FIELD_NUMBER: _ClassVar[int]
    NEGATIVEX21SET_FIELD_NUMBER: _ClassVar[int]
    POSITIVER12NULL_FIELD_NUMBER: _ClassVar[int]
    POSITIVER12SET_FIELD_NUMBER: _ClassVar[int]
    POSITIVER21NULL_FIELD_NUMBER: _ClassVar[int]
    POSITIVER21SET_FIELD_NUMBER: _ClassVar[int]
    POSITIVEX12NULL_FIELD_NUMBER: _ClassVar[int]
    POSITIVEX12SET_FIELD_NUMBER: _ClassVar[int]
    POSITIVEX21NULL_FIELD_NUMBER: _ClassVar[int]
    POSITIVEX21SET_FIELD_NUMBER: _ClassVar[int]
    RNULL_FIELD_NUMBER: _ClassVar[int]
    RSET_FIELD_NUMBER: _ClassVar[int]
    R21NULL_FIELD_NUMBER: _ClassVar[int]
    R21SET_FIELD_NUMBER: _ClassVar[int]
    XNULL_FIELD_NUMBER: _ClassVar[int]
    XSET_FIELD_NUMBER: _ClassVar[int]
    X21NULL_FIELD_NUMBER: _ClassVar[int]
    X21SET_FIELD_NUMBER: _ClassVar[int]
    ZEROR12NULL_FIELD_NUMBER: _ClassVar[int]
    ZEROR12SET_FIELD_NUMBER: _ClassVar[int]
    ZEROR21NULL_FIELD_NUMBER: _ClassVar[int]
    ZEROR21SET_FIELD_NUMBER: _ClassVar[int]
    ZEROX12NULL_FIELD_NUMBER: _ClassVar[int]
    ZEROX12SET_FIELD_NUMBER: _ClassVar[int]
    ZEROX21NULL_FIELD_NUMBER: _ClassVar[int]
    ZEROX21SET_FIELD_NUMBER: _ClassVar[int]
    ee: _EquivalentEquipment_pb2.EquivalentEquipment
    negativeR12Null: _struct_pb2.NullValue
    negativeR12Set: float
    negativeR21Null: _struct_pb2.NullValue
    negativeR21Set: float
    negativeX12Null: _struct_pb2.NullValue
    negativeX12Set: float
    negativeX21Null: _struct_pb2.NullValue
    negativeX21Set: float
    positiveR12Null: _struct_pb2.NullValue
    positiveR12Set: float
    positiveR21Null: _struct_pb2.NullValue
    positiveR21Set: float
    positiveX12Null: _struct_pb2.NullValue
    positiveX12Set: float
    positiveX21Null: _struct_pb2.NullValue
    positiveX21Set: float
    rNull: _struct_pb2.NullValue
    rSet: float
    r21Null: _struct_pb2.NullValue
    r21Set: float
    xNull: _struct_pb2.NullValue
    xSet: float
    x21Null: _struct_pb2.NullValue
    x21Set: float
    zeroR12Null: _struct_pb2.NullValue
    zeroR12Set: float
    zeroR21Null: _struct_pb2.NullValue
    zeroR21Set: float
    zeroX12Null: _struct_pb2.NullValue
    zeroX12Set: float
    zeroX21Null: _struct_pb2.NullValue
    zeroX21Set: float
    def __init__(self, ee: _Optional[_Union[_EquivalentEquipment_pb2.EquivalentEquipment, _Mapping]] = ..., negativeR12Null: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., negativeR12Set: _Optional[float] = ..., negativeR21Null: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., negativeR21Set: _Optional[float] = ..., negativeX12Null: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., negativeX12Set: _Optional[float] = ..., negativeX21Null: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., negativeX21Set: _Optional[float] = ..., positiveR12Null: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., positiveR12Set: _Optional[float] = ..., positiveR21Null: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., positiveR21Set: _Optional[float] = ..., positiveX12Null: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., positiveX12Set: _Optional[float] = ..., positiveX21Null: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., positiveX21Set: _Optional[float] = ..., rNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., rSet: _Optional[float] = ..., r21Null: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., r21Set: _Optional[float] = ..., xNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., xSet: _Optional[float] = ..., x21Null: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., x21Set: _Optional[float] = ..., zeroR12Null: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., zeroR12Set: _Optional[float] = ..., zeroR21Null: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., zeroR21Set: _Optional[float] = ..., zeroX12Null: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., zeroX12Set: _Optional[float] = ..., zeroX21Null: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., zeroX21Set: _Optional[float] = ...) -> None: ...
