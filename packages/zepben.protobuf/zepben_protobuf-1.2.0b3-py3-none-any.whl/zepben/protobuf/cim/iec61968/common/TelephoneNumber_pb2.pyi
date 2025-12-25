from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class TelephoneNumber(_message.Message):
    __slots__ = ("areaCodeNull", "areaCodeSet", "cityCodeNull", "cityCodeSet", "countryCodeNull", "countryCodeSet", "dialOutNull", "dialOutSet", "extensionNull", "extensionSet", "internationalPrefixNull", "internationalPrefixSet", "localNumberNull", "localNumberSet", "isPrimaryNull", "isPrimarySet", "descriptionNull", "descriptionSet")
    AREACODENULL_FIELD_NUMBER: _ClassVar[int]
    AREACODESET_FIELD_NUMBER: _ClassVar[int]
    CITYCODENULL_FIELD_NUMBER: _ClassVar[int]
    CITYCODESET_FIELD_NUMBER: _ClassVar[int]
    COUNTRYCODENULL_FIELD_NUMBER: _ClassVar[int]
    COUNTRYCODESET_FIELD_NUMBER: _ClassVar[int]
    DIALOUTNULL_FIELD_NUMBER: _ClassVar[int]
    DIALOUTSET_FIELD_NUMBER: _ClassVar[int]
    EXTENSIONNULL_FIELD_NUMBER: _ClassVar[int]
    EXTENSIONSET_FIELD_NUMBER: _ClassVar[int]
    INTERNATIONALPREFIXNULL_FIELD_NUMBER: _ClassVar[int]
    INTERNATIONALPREFIXSET_FIELD_NUMBER: _ClassVar[int]
    LOCALNUMBERNULL_FIELD_NUMBER: _ClassVar[int]
    LOCALNUMBERSET_FIELD_NUMBER: _ClassVar[int]
    ISPRIMARYNULL_FIELD_NUMBER: _ClassVar[int]
    ISPRIMARYSET_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTIONNULL_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTIONSET_FIELD_NUMBER: _ClassVar[int]
    areaCodeNull: _struct_pb2.NullValue
    areaCodeSet: str
    cityCodeNull: _struct_pb2.NullValue
    cityCodeSet: str
    countryCodeNull: _struct_pb2.NullValue
    countryCodeSet: str
    dialOutNull: _struct_pb2.NullValue
    dialOutSet: str
    extensionNull: _struct_pb2.NullValue
    extensionSet: str
    internationalPrefixNull: _struct_pb2.NullValue
    internationalPrefixSet: str
    localNumberNull: _struct_pb2.NullValue
    localNumberSet: str
    isPrimaryNull: _struct_pb2.NullValue
    isPrimarySet: bool
    descriptionNull: _struct_pb2.NullValue
    descriptionSet: str
    def __init__(self, areaCodeNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., areaCodeSet: _Optional[str] = ..., cityCodeNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., cityCodeSet: _Optional[str] = ..., countryCodeNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., countryCodeSet: _Optional[str] = ..., dialOutNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., dialOutSet: _Optional[str] = ..., extensionNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., extensionSet: _Optional[str] = ..., internationalPrefixNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., internationalPrefixSet: _Optional[str] = ..., localNumberNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., localNumberSet: _Optional[str] = ..., isPrimaryNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., isPrimarySet: bool = ..., descriptionNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., descriptionSet: _Optional[str] = ...) -> None: ...
