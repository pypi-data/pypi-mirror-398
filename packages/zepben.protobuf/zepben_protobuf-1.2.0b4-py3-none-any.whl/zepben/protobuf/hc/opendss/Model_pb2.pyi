from google.protobuf import struct_pb2 as _struct_pb2
from zepben.protobuf.hc import Syf_pb2 as _Syf_pb2
from zepben.protobuf.hc.opendss import LoadShape_pb2 as _LoadShape_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class MaybeModel(_message.Message):
    __slots__ = ("modelNull", "modelSet")
    MODELNULL_FIELD_NUMBER: _ClassVar[int]
    MODELSET_FIELD_NUMBER: _ClassVar[int]
    modelNull: _struct_pb2.NullValue
    modelSet: Model
    def __init__(self, modelNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., modelSet: _Optional[_Union[Model, _Mapping]] = ...) -> None: ...

class Model(_message.Message):
    __slots__ = ("syf", "preLoadShapeCommand", "loadShapes", "postLoadShapeCommand")
    SYF_FIELD_NUMBER: _ClassVar[int]
    PRELOADSHAPECOMMAND_FIELD_NUMBER: _ClassVar[int]
    LOADSHAPES_FIELD_NUMBER: _ClassVar[int]
    POSTLOADSHAPECOMMAND_FIELD_NUMBER: _ClassVar[int]
    syf: _Syf_pb2.Syf
    preLoadShapeCommand: _containers.RepeatedScalarFieldContainer[str]
    loadShapes: _containers.RepeatedCompositeFieldContainer[_LoadShape_pb2.LoadShape]
    postLoadShapeCommand: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, syf: _Optional[_Union[_Syf_pb2.Syf, _Mapping]] = ..., preLoadShapeCommand: _Optional[_Iterable[str]] = ..., loadShapes: _Optional[_Iterable[_Union[_LoadShape_pb2.LoadShape, _Mapping]]] = ..., postLoadShapeCommand: _Optional[_Iterable[str]] = ...) -> None: ...
