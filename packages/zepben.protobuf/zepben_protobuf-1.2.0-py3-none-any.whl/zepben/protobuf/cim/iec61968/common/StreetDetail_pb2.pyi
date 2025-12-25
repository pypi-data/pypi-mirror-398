from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class StreetDetail(_message.Message):
    __slots__ = ("buildingNameNull", "buildingNameSet", "floorIdentificationNull", "floorIdentificationSet", "nameNull", "nameSet", "numberNull", "numberSet", "suiteNumberNull", "suiteNumberSet", "typeNull", "typeSet", "displayAddressNull", "displayAddressSet", "buildingNumberNull", "buildingNumberSet")
    BUILDINGNAMENULL_FIELD_NUMBER: _ClassVar[int]
    BUILDINGNAMESET_FIELD_NUMBER: _ClassVar[int]
    FLOORIDENTIFICATIONNULL_FIELD_NUMBER: _ClassVar[int]
    FLOORIDENTIFICATIONSET_FIELD_NUMBER: _ClassVar[int]
    NAMENULL_FIELD_NUMBER: _ClassVar[int]
    NAMESET_FIELD_NUMBER: _ClassVar[int]
    NUMBERNULL_FIELD_NUMBER: _ClassVar[int]
    NUMBERSET_FIELD_NUMBER: _ClassVar[int]
    SUITENUMBERNULL_FIELD_NUMBER: _ClassVar[int]
    SUITENUMBERSET_FIELD_NUMBER: _ClassVar[int]
    TYPENULL_FIELD_NUMBER: _ClassVar[int]
    TYPESET_FIELD_NUMBER: _ClassVar[int]
    DISPLAYADDRESSNULL_FIELD_NUMBER: _ClassVar[int]
    DISPLAYADDRESSSET_FIELD_NUMBER: _ClassVar[int]
    BUILDINGNUMBERNULL_FIELD_NUMBER: _ClassVar[int]
    BUILDINGNUMBERSET_FIELD_NUMBER: _ClassVar[int]
    buildingNameNull: _struct_pb2.NullValue
    buildingNameSet: str
    floorIdentificationNull: _struct_pb2.NullValue
    floorIdentificationSet: str
    nameNull: _struct_pb2.NullValue
    nameSet: str
    numberNull: _struct_pb2.NullValue
    numberSet: str
    suiteNumberNull: _struct_pb2.NullValue
    suiteNumberSet: str
    typeNull: _struct_pb2.NullValue
    typeSet: str
    displayAddressNull: _struct_pb2.NullValue
    displayAddressSet: str
    buildingNumberNull: _struct_pb2.NullValue
    buildingNumberSet: str
    def __init__(self, buildingNameNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., buildingNameSet: _Optional[str] = ..., floorIdentificationNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., floorIdentificationSet: _Optional[str] = ..., nameNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., nameSet: _Optional[str] = ..., numberNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., numberSet: _Optional[str] = ..., suiteNumberNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., suiteNumberSet: _Optional[str] = ..., typeNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., typeSet: _Optional[str] = ..., displayAddressNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., displayAddressSet: _Optional[str] = ..., buildingNumberNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., buildingNumberSet: _Optional[str] = ...) -> None: ...
