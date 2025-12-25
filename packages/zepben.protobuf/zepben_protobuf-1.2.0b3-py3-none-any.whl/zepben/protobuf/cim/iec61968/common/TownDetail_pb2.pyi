from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class TownDetail(_message.Message):
    __slots__ = ("nameNull", "nameSet", "stateOrProvinceNull", "stateOrProvinceSet", "countryNull", "countrySet")
    NAMENULL_FIELD_NUMBER: _ClassVar[int]
    NAMESET_FIELD_NUMBER: _ClassVar[int]
    STATEORPROVINCENULL_FIELD_NUMBER: _ClassVar[int]
    STATEORPROVINCESET_FIELD_NUMBER: _ClassVar[int]
    COUNTRYNULL_FIELD_NUMBER: _ClassVar[int]
    COUNTRYSET_FIELD_NUMBER: _ClassVar[int]
    nameNull: _struct_pb2.NullValue
    nameSet: str
    stateOrProvinceNull: _struct_pb2.NullValue
    stateOrProvinceSet: str
    countryNull: _struct_pb2.NullValue
    countrySet: str
    def __init__(self, nameNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., nameSet: _Optional[str] = ..., stateOrProvinceNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., stateOrProvinceSet: _Optional[str] = ..., countryNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., countrySet: _Optional[str] = ...) -> None: ...
