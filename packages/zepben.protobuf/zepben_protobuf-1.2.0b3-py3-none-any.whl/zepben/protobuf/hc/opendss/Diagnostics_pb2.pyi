from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SummaryReport(_message.Message):
    __slots__ = ("caseName", "solved", "mode", "number", "loadMult", "numDevices", "numBuses", "numNodes", "iterations", "controlMode", "controlIterations", "mostIterationsDone", "year", "hour", "maxPuVoltage", "minPuVoltage", "totalMW", "totalMvar", "mwLosses", "pctLosses", "mvarLosses", "frequency")
    CASENAME_FIELD_NUMBER: _ClassVar[int]
    SOLVED_FIELD_NUMBER: _ClassVar[int]
    MODE_FIELD_NUMBER: _ClassVar[int]
    NUMBER_FIELD_NUMBER: _ClassVar[int]
    LOADMULT_FIELD_NUMBER: _ClassVar[int]
    NUMDEVICES_FIELD_NUMBER: _ClassVar[int]
    NUMBUSES_FIELD_NUMBER: _ClassVar[int]
    NUMNODES_FIELD_NUMBER: _ClassVar[int]
    ITERATIONS_FIELD_NUMBER: _ClassVar[int]
    CONTROLMODE_FIELD_NUMBER: _ClassVar[int]
    CONTROLITERATIONS_FIELD_NUMBER: _ClassVar[int]
    MOSTITERATIONSDONE_FIELD_NUMBER: _ClassVar[int]
    YEAR_FIELD_NUMBER: _ClassVar[int]
    HOUR_FIELD_NUMBER: _ClassVar[int]
    MAXPUVOLTAGE_FIELD_NUMBER: _ClassVar[int]
    MINPUVOLTAGE_FIELD_NUMBER: _ClassVar[int]
    TOTALMW_FIELD_NUMBER: _ClassVar[int]
    TOTALMVAR_FIELD_NUMBER: _ClassVar[int]
    MWLOSSES_FIELD_NUMBER: _ClassVar[int]
    PCTLOSSES_FIELD_NUMBER: _ClassVar[int]
    MVARLOSSES_FIELD_NUMBER: _ClassVar[int]
    FREQUENCY_FIELD_NUMBER: _ClassVar[int]
    caseName: str
    solved: bool
    mode: str
    number: int
    loadMult: float
    numDevices: int
    numBuses: int
    numNodes: int
    iterations: int
    controlMode: str
    controlIterations: int
    mostIterationsDone: int
    year: int
    hour: int
    maxPuVoltage: float
    minPuVoltage: float
    totalMW: float
    totalMvar: float
    mwLosses: float
    pctLosses: float
    mvarLosses: float
    frequency: float
    def __init__(self, caseName: _Optional[str] = ..., solved: bool = ..., mode: _Optional[str] = ..., number: _Optional[int] = ..., loadMult: _Optional[float] = ..., numDevices: _Optional[int] = ..., numBuses: _Optional[int] = ..., numNodes: _Optional[int] = ..., iterations: _Optional[int] = ..., controlMode: _Optional[str] = ..., controlIterations: _Optional[int] = ..., mostIterationsDone: _Optional[int] = ..., year: _Optional[int] = ..., hour: _Optional[int] = ..., maxPuVoltage: _Optional[float] = ..., minPuVoltage: _Optional[float] = ..., totalMW: _Optional[float] = ..., totalMvar: _Optional[float] = ..., mwLosses: _Optional[float] = ..., pctLosses: _Optional[float] = ..., mvarLosses: _Optional[float] = ..., frequency: _Optional[float] = ...) -> None: ...

class EventLogEntry(_message.Message):
    __slots__ = ("hour", "sec", "controlIter", "iteration", "element", "action", "event")
    HOUR_FIELD_NUMBER: _ClassVar[int]
    SEC_FIELD_NUMBER: _ClassVar[int]
    CONTROLITER_FIELD_NUMBER: _ClassVar[int]
    ITERATION_FIELD_NUMBER: _ClassVar[int]
    ELEMENT_FIELD_NUMBER: _ClassVar[int]
    ACTION_FIELD_NUMBER: _ClassVar[int]
    EVENT_FIELD_NUMBER: _ClassVar[int]
    hour: int
    sec: float
    controlIter: int
    iteration: int
    element: str
    action: str
    event: str
    def __init__(self, hour: _Optional[int] = ..., sec: _Optional[float] = ..., controlIter: _Optional[int] = ..., iteration: _Optional[int] = ..., element: _Optional[str] = ..., action: _Optional[str] = ..., event: _Optional[str] = ...) -> None: ...

class EventLog(_message.Message):
    __slots__ = ("logEntry",)
    LOGENTRY_FIELD_NUMBER: _ClassVar[int]
    logEntry: _containers.RepeatedCompositeFieldContainer[EventLogEntry]
    def __init__(self, logEntry: _Optional[_Iterable[_Union[EventLogEntry, _Mapping]]] = ...) -> None: ...

class TapsReport(_message.Message):
    __slots__ = ("name", "tap", "min", "max", "step", "position")
    NAME_FIELD_NUMBER: _ClassVar[int]
    TAP_FIELD_NUMBER: _ClassVar[int]
    MIN_FIELD_NUMBER: _ClassVar[int]
    MAX_FIELD_NUMBER: _ClassVar[int]
    STEP_FIELD_NUMBER: _ClassVar[int]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    name: str
    tap: float
    min: float
    max: float
    step: float
    position: int
    def __init__(self, name: _Optional[str] = ..., tap: _Optional[float] = ..., min: _Optional[float] = ..., max: _Optional[float] = ..., step: _Optional[float] = ..., position: _Optional[int] = ...) -> None: ...

class LoopReport(_message.Message):
    __slots__ = ("meter", "lineA", "lineB", "parallel", "looped")
    METER_FIELD_NUMBER: _ClassVar[int]
    LINEA_FIELD_NUMBER: _ClassVar[int]
    LINEB_FIELD_NUMBER: _ClassVar[int]
    PARALLEL_FIELD_NUMBER: _ClassVar[int]
    LOOPED_FIELD_NUMBER: _ClassVar[int]
    meter: str
    lineA: str
    lineB: str
    parallel: bool
    looped: bool
    def __init__(self, meter: _Optional[str] = ..., lineA: _Optional[str] = ..., lineB: _Optional[str] = ..., parallel: bool = ..., looped: bool = ...) -> None: ...

class IsolatedArea(_message.Message):
    __slots__ = ("level", "element", "loads")
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    ELEMENT_FIELD_NUMBER: _ClassVar[int]
    LOADS_FIELD_NUMBER: _ClassVar[int]
    level: int
    element: str
    loads: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, level: _Optional[int] = ..., element: _Optional[str] = ..., loads: _Optional[_Iterable[str]] = ...) -> None: ...

class IsolatedElement(_message.Message):
    __slots__ = ("name", "buses")
    NAME_FIELD_NUMBER: _ClassVar[int]
    BUSES_FIELD_NUMBER: _ClassVar[int]
    name: str
    buses: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, name: _Optional[str] = ..., buses: _Optional[_Iterable[str]] = ...) -> None: ...

class IsolatedBusesReport(_message.Message):
    __slots__ = ("disconnectedBuses", "isolatedSubAreas", "isolatedElements")
    DISCONNECTEDBUSES_FIELD_NUMBER: _ClassVar[int]
    ISOLATEDSUBAREAS_FIELD_NUMBER: _ClassVar[int]
    ISOLATEDELEMENTS_FIELD_NUMBER: _ClassVar[int]
    disconnectedBuses: _containers.RepeatedScalarFieldContainer[str]
    isolatedSubAreas: _containers.RepeatedCompositeFieldContainer[IsolatedArea]
    isolatedElements: _containers.RepeatedCompositeFieldContainer[IsolatedElement]
    def __init__(self, disconnectedBuses: _Optional[_Iterable[str]] = ..., isolatedSubAreas: _Optional[_Iterable[_Union[IsolatedArea, _Mapping]]] = ..., isolatedElements: _Optional[_Iterable[_Union[IsolatedElement, _Mapping]]] = ...) -> None: ...

class LossesEntry(_message.Message):
    __slots__ = ("element", "kwLosses", "pctPower", "kvarLosses")
    ELEMENT_FIELD_NUMBER: _ClassVar[int]
    KWLOSSES_FIELD_NUMBER: _ClassVar[int]
    PCTPOWER_FIELD_NUMBER: _ClassVar[int]
    KVARLOSSES_FIELD_NUMBER: _ClassVar[int]
    element: str
    kwLosses: float
    pctPower: float
    kvarLosses: float
    def __init__(self, element: _Optional[str] = ..., kwLosses: _Optional[float] = ..., pctPower: _Optional[float] = ..., kvarLosses: _Optional[float] = ...) -> None: ...

class LossesTotals(_message.Message):
    __slots__ = ("lineLosses", "transformerLosses", "totalLosses", "totalLoadPower", "totalPctLosses")
    LINELOSSES_FIELD_NUMBER: _ClassVar[int]
    TRANSFORMERLOSSES_FIELD_NUMBER: _ClassVar[int]
    TOTALLOSSES_FIELD_NUMBER: _ClassVar[int]
    TOTALLOADPOWER_FIELD_NUMBER: _ClassVar[int]
    TOTALPCTLOSSES_FIELD_NUMBER: _ClassVar[int]
    lineLosses: float
    transformerLosses: float
    totalLosses: float
    totalLoadPower: float
    totalPctLosses: float
    def __init__(self, lineLosses: _Optional[float] = ..., transformerLosses: _Optional[float] = ..., totalLosses: _Optional[float] = ..., totalLoadPower: _Optional[float] = ..., totalPctLosses: _Optional[float] = ...) -> None: ...

class NodeMismatch(_message.Message):
    __slots__ = ("bus", "node", "currentSum", "pctError", "maxCurrent")
    BUS_FIELD_NUMBER: _ClassVar[int]
    NODE_FIELD_NUMBER: _ClassVar[int]
    CURRENTSUM_FIELD_NUMBER: _ClassVar[int]
    PCTERROR_FIELD_NUMBER: _ClassVar[int]
    MAXCURRENT_FIELD_NUMBER: _ClassVar[int]
    bus: str
    node: int
    currentSum: float
    pctError: float
    maxCurrent: float
    def __init__(self, bus: _Optional[str] = ..., node: _Optional[int] = ..., currentSum: _Optional[float] = ..., pctError: _Optional[float] = ..., maxCurrent: _Optional[float] = ...) -> None: ...

class KVBaseMismatch(_message.Message):
    __slots__ = ("load", "kv", "bus", "kvBase")
    LOAD_FIELD_NUMBER: _ClassVar[int]
    KV_FIELD_NUMBER: _ClassVar[int]
    BUS_FIELD_NUMBER: _ClassVar[int]
    KVBASE_FIELD_NUMBER: _ClassVar[int]
    load: str
    kv: float
    bus: str
    kvBase: float
    def __init__(self, load: _Optional[str] = ..., kv: _Optional[float] = ..., bus: _Optional[str] = ..., kvBase: _Optional[float] = ...) -> None: ...
