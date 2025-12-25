from zepben.protobuf.cim.iec61968.assets import Asset_pb2 as _Asset_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AssetContainer(_message.Message):
    __slots__ = ("at",)
    AT_FIELD_NUMBER: _ClassVar[int]
    at: _Asset_pb2.Asset
    def __init__(self, at: _Optional[_Union[_Asset_pb2.Asset, _Mapping]] = ...) -> None: ...
