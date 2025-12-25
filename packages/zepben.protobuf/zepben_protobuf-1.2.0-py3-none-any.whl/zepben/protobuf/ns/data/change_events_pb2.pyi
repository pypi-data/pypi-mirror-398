from google.protobuf import timestamp_pb2 as _timestamp_pb2
from zepben.protobuf.cim.iec61970.base.core import PhaseCode_pb2 as _PhaseCode_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SwitchAction(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SWITCH_ACTION_UNKNOWN: _ClassVar[SwitchAction]
    SWITCH_ACTION_OPEN: _ClassVar[SwitchAction]
    SWITCH_ACTION_CLOSE: _ClassVar[SwitchAction]
SWITCH_ACTION_UNKNOWN: SwitchAction
SWITCH_ACTION_OPEN: SwitchAction
SWITCH_ACTION_CLOSE: SwitchAction

class CurrentStateEvent(_message.Message):
    __slots__ = ("eventId", "timestamp", "switch", "addCut", "removeCut", "addJumper", "removeJumper")
    EVENTID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    SWITCH_FIELD_NUMBER: _ClassVar[int]
    ADDCUT_FIELD_NUMBER: _ClassVar[int]
    REMOVECUT_FIELD_NUMBER: _ClassVar[int]
    ADDJUMPER_FIELD_NUMBER: _ClassVar[int]
    REMOVEJUMPER_FIELD_NUMBER: _ClassVar[int]
    eventId: str
    timestamp: _timestamp_pb2.Timestamp
    switch: SwitchStateEvent
    addCut: AddCutEvent
    removeCut: RemoveCutEvent
    addJumper: AddJumperEvent
    removeJumper: RemoveJumperEvent
    def __init__(self, eventId: _Optional[str] = ..., timestamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., switch: _Optional[_Union[SwitchStateEvent, _Mapping]] = ..., addCut: _Optional[_Union[AddCutEvent, _Mapping]] = ..., removeCut: _Optional[_Union[RemoveCutEvent, _Mapping]] = ..., addJumper: _Optional[_Union[AddJumperEvent, _Mapping]] = ..., removeJumper: _Optional[_Union[RemoveJumperEvent, _Mapping]] = ...) -> None: ...

class SwitchStateEvent(_message.Message):
    __slots__ = ("mRID", "action", "phases")
    MRID_FIELD_NUMBER: _ClassVar[int]
    ACTION_FIELD_NUMBER: _ClassVar[int]
    PHASES_FIELD_NUMBER: _ClassVar[int]
    mRID: str
    action: SwitchAction
    phases: _PhaseCode_pb2.PhaseCode
    def __init__(self, mRID: _Optional[str] = ..., action: _Optional[_Union[SwitchAction, str]] = ..., phases: _Optional[_Union[_PhaseCode_pb2.PhaseCode, str]] = ...) -> None: ...

class AddCutEvent(_message.Message):
    __slots__ = ("mRID", "aclsMRID")
    MRID_FIELD_NUMBER: _ClassVar[int]
    ACLSMRID_FIELD_NUMBER: _ClassVar[int]
    mRID: str
    aclsMRID: str
    def __init__(self, mRID: _Optional[str] = ..., aclsMRID: _Optional[str] = ...) -> None: ...

class RemoveCutEvent(_message.Message):
    __slots__ = ("mRID",)
    MRID_FIELD_NUMBER: _ClassVar[int]
    mRID: str
    def __init__(self, mRID: _Optional[str] = ...) -> None: ...

class AddJumperEvent(_message.Message):
    __slots__ = ("mRID", "fromConnection", "toConnection")
    MRID_FIELD_NUMBER: _ClassVar[int]
    FROMCONNECTION_FIELD_NUMBER: _ClassVar[int]
    TOCONNECTION_FIELD_NUMBER: _ClassVar[int]
    mRID: str
    fromConnection: JumperConnection
    toConnection: JumperConnection
    def __init__(self, mRID: _Optional[str] = ..., fromConnection: _Optional[_Union[JumperConnection, _Mapping]] = ..., toConnection: _Optional[_Union[JumperConnection, _Mapping]] = ...) -> None: ...

class RemoveJumperEvent(_message.Message):
    __slots__ = ("mRID",)
    MRID_FIELD_NUMBER: _ClassVar[int]
    mRID: str
    def __init__(self, mRID: _Optional[str] = ...) -> None: ...

class JumperConnection(_message.Message):
    __slots__ = ("connectedMRID",)
    CONNECTEDMRID_FIELD_NUMBER: _ClassVar[int]
    connectedMRID: str
    def __init__(self, connectedMRID: _Optional[str] = ...) -> None: ...
