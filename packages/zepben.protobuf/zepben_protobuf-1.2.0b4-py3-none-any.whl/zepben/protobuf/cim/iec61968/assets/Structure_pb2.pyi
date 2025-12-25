from zepben.protobuf.cim.iec61968.assets import AssetContainer_pb2 as _AssetContainer_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Structure(_message.Message):
    __slots__ = ("ac",)
    AC_FIELD_NUMBER: _ClassVar[int]
    ac: _AssetContainer_pb2.AssetContainer
    def __init__(self, ac: _Optional[_Union[_AssetContainer_pb2.AssetContainer, _Mapping]] = ...) -> None: ...
