from zepben.protobuf.cim.extensions.iec61970.base.wires import VectorGroup_pb2 as _VectorGroup_pb2
from zepben.protobuf.cim.iec61968.infiec61968.infassetinfo import TransformerConstructionKind_pb2 as _TransformerConstructionKind_pb2
from zepben.protobuf.cim.iec61968.infiec61968.infassetinfo import TransformerFunctionKind_pb2 as _TransformerFunctionKind_pb2
from zepben.protobuf.cim.iec61970.base.core import ConductingEquipment_pb2 as _ConductingEquipment_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PowerTransformer(_message.Message):
    __slots__ = ("ce", "powerTransformerEndMRIDs", "vectorGroup", "transformerUtilisationNull", "transformerUtilisationSet", "constructionKind", "function")
    CE_FIELD_NUMBER: _ClassVar[int]
    POWERTRANSFORMERENDMRIDS_FIELD_NUMBER: _ClassVar[int]
    VECTORGROUP_FIELD_NUMBER: _ClassVar[int]
    TRANSFORMERUTILISATIONNULL_FIELD_NUMBER: _ClassVar[int]
    TRANSFORMERUTILISATIONSET_FIELD_NUMBER: _ClassVar[int]
    CONSTRUCTIONKIND_FIELD_NUMBER: _ClassVar[int]
    FUNCTION_FIELD_NUMBER: _ClassVar[int]
    ce: _ConductingEquipment_pb2.ConductingEquipment
    powerTransformerEndMRIDs: _containers.RepeatedScalarFieldContainer[str]
    vectorGroup: _VectorGroup_pb2.VectorGroup
    transformerUtilisationNull: _struct_pb2.NullValue
    transformerUtilisationSet: float
    constructionKind: _TransformerConstructionKind_pb2.TransformerConstructionKind
    function: _TransformerFunctionKind_pb2.TransformerFunctionKind
    def __init__(self, ce: _Optional[_Union[_ConductingEquipment_pb2.ConductingEquipment, _Mapping]] = ..., powerTransformerEndMRIDs: _Optional[_Iterable[str]] = ..., vectorGroup: _Optional[_Union[_VectorGroup_pb2.VectorGroup, str]] = ..., transformerUtilisationNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., transformerUtilisationSet: _Optional[float] = ..., constructionKind: _Optional[_Union[_TransformerConstructionKind_pb2.TransformerConstructionKind, str]] = ..., function: _Optional[_Union[_TransformerFunctionKind_pb2.TransformerFunctionKind, str]] = ...) -> None: ...
