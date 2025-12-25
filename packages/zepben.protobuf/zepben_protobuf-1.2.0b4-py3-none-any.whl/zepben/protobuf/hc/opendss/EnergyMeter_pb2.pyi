from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class VoltBaseRegisters(_message.Message):
    __slots__ = ("vbase", "kvLosses", "kvLineLoss", "kvLoadLoss", "kvNoLoadLoss", "kvLoadEnergy")
    VBASE_FIELD_NUMBER: _ClassVar[int]
    KVLOSSES_FIELD_NUMBER: _ClassVar[int]
    KVLINELOSS_FIELD_NUMBER: _ClassVar[int]
    KVLOADLOSS_FIELD_NUMBER: _ClassVar[int]
    KVNOLOADLOSS_FIELD_NUMBER: _ClassVar[int]
    KVLOADENERGY_FIELD_NUMBER: _ClassVar[int]
    vbase: float
    kvLosses: float
    kvLineLoss: float
    kvLoadLoss: float
    kvNoLoadLoss: float
    kvLoadEnergy: float
    def __init__(self, vbase: _Optional[float] = ..., kvLosses: _Optional[float] = ..., kvLineLoss: _Optional[float] = ..., kvLoadLoss: _Optional[float] = ..., kvNoLoadLoss: _Optional[float] = ..., kvLoadEnergy: _Optional[float] = ...) -> None: ...

class DemandIntervalReport(_message.Message):
    __slots__ = ("element", "hour", "kwh", "kvarh", "maxKw", "maxKva", "zoneKwh", "zoneKvarh", "zoneMaxKw", "zoneMaxKva", "overloadKwhNormal", "overloadKwhEmerg", "loadEEN", "loadUE", "zoneLossesKwh", "zoneLossesKvarh", "zoneMaxKwLosses", "zoneMaxKvarLosses", "loadLossesKwh", "loadLossesKvarh", "noLoadLossesKwh", "noLoadLossesKvarh", "maxKwLoadLosses", "maxKwNoLoadLosses", "lineLosses", "transformerLosses", "lineModeLineLosses", "zeroModeLineLosses", "phaseLineLosses3", "phaseLineLosses12", "genKwh", "genKvarh", "genMaxKw", "genMaxKva", "voltBases")
    ELEMENT_FIELD_NUMBER: _ClassVar[int]
    HOUR_FIELD_NUMBER: _ClassVar[int]
    KWH_FIELD_NUMBER: _ClassVar[int]
    KVARH_FIELD_NUMBER: _ClassVar[int]
    MAXKW_FIELD_NUMBER: _ClassVar[int]
    MAXKVA_FIELD_NUMBER: _ClassVar[int]
    ZONEKWH_FIELD_NUMBER: _ClassVar[int]
    ZONEKVARH_FIELD_NUMBER: _ClassVar[int]
    ZONEMAXKW_FIELD_NUMBER: _ClassVar[int]
    ZONEMAXKVA_FIELD_NUMBER: _ClassVar[int]
    OVERLOADKWHNORMAL_FIELD_NUMBER: _ClassVar[int]
    OVERLOADKWHEMERG_FIELD_NUMBER: _ClassVar[int]
    LOADEEN_FIELD_NUMBER: _ClassVar[int]
    LOADUE_FIELD_NUMBER: _ClassVar[int]
    ZONELOSSESKWH_FIELD_NUMBER: _ClassVar[int]
    ZONELOSSESKVARH_FIELD_NUMBER: _ClassVar[int]
    ZONEMAXKWLOSSES_FIELD_NUMBER: _ClassVar[int]
    ZONEMAXKVARLOSSES_FIELD_NUMBER: _ClassVar[int]
    LOADLOSSESKWH_FIELD_NUMBER: _ClassVar[int]
    LOADLOSSESKVARH_FIELD_NUMBER: _ClassVar[int]
    NOLOADLOSSESKWH_FIELD_NUMBER: _ClassVar[int]
    NOLOADLOSSESKVARH_FIELD_NUMBER: _ClassVar[int]
    MAXKWLOADLOSSES_FIELD_NUMBER: _ClassVar[int]
    MAXKWNOLOADLOSSES_FIELD_NUMBER: _ClassVar[int]
    LINELOSSES_FIELD_NUMBER: _ClassVar[int]
    TRANSFORMERLOSSES_FIELD_NUMBER: _ClassVar[int]
    LINEMODELINELOSSES_FIELD_NUMBER: _ClassVar[int]
    ZEROMODELINELOSSES_FIELD_NUMBER: _ClassVar[int]
    PHASELINELOSSES3_FIELD_NUMBER: _ClassVar[int]
    PHASELINELOSSES12_FIELD_NUMBER: _ClassVar[int]
    GENKWH_FIELD_NUMBER: _ClassVar[int]
    GENKVARH_FIELD_NUMBER: _ClassVar[int]
    GENMAXKW_FIELD_NUMBER: _ClassVar[int]
    GENMAXKVA_FIELD_NUMBER: _ClassVar[int]
    VOLTBASES_FIELD_NUMBER: _ClassVar[int]
    element: str
    hour: float
    kwh: float
    kvarh: float
    maxKw: float
    maxKva: float
    zoneKwh: float
    zoneKvarh: float
    zoneMaxKw: float
    zoneMaxKva: float
    overloadKwhNormal: float
    overloadKwhEmerg: float
    loadEEN: float
    loadUE: float
    zoneLossesKwh: float
    zoneLossesKvarh: float
    zoneMaxKwLosses: float
    zoneMaxKvarLosses: float
    loadLossesKwh: float
    loadLossesKvarh: float
    noLoadLossesKwh: float
    noLoadLossesKvarh: float
    maxKwLoadLosses: float
    maxKwNoLoadLosses: float
    lineLosses: float
    transformerLosses: float
    lineModeLineLosses: float
    zeroModeLineLosses: float
    phaseLineLosses3: float
    phaseLineLosses12: float
    genKwh: float
    genKvarh: float
    genMaxKw: float
    genMaxKva: float
    voltBases: _containers.RepeatedCompositeFieldContainer[VoltBaseRegisters]
    def __init__(self, element: _Optional[str] = ..., hour: _Optional[float] = ..., kwh: _Optional[float] = ..., kvarh: _Optional[float] = ..., maxKw: _Optional[float] = ..., maxKva: _Optional[float] = ..., zoneKwh: _Optional[float] = ..., zoneKvarh: _Optional[float] = ..., zoneMaxKw: _Optional[float] = ..., zoneMaxKva: _Optional[float] = ..., overloadKwhNormal: _Optional[float] = ..., overloadKwhEmerg: _Optional[float] = ..., loadEEN: _Optional[float] = ..., loadUE: _Optional[float] = ..., zoneLossesKwh: _Optional[float] = ..., zoneLossesKvarh: _Optional[float] = ..., zoneMaxKwLosses: _Optional[float] = ..., zoneMaxKvarLosses: _Optional[float] = ..., loadLossesKwh: _Optional[float] = ..., loadLossesKvarh: _Optional[float] = ..., noLoadLossesKwh: _Optional[float] = ..., noLoadLossesKvarh: _Optional[float] = ..., maxKwLoadLosses: _Optional[float] = ..., maxKwNoLoadLosses: _Optional[float] = ..., lineLosses: _Optional[float] = ..., transformerLosses: _Optional[float] = ..., lineModeLineLosses: _Optional[float] = ..., zeroModeLineLosses: _Optional[float] = ..., phaseLineLosses3: _Optional[float] = ..., phaseLineLosses12: _Optional[float] = ..., genKwh: _Optional[float] = ..., genKvarh: _Optional[float] = ..., genMaxKw: _Optional[float] = ..., genMaxKva: _Optional[float] = ..., voltBases: _Optional[_Iterable[_Union[VoltBaseRegisters, _Mapping]]] = ...) -> None: ...

class MaxMinAvg(_message.Message):
    __slots__ = ("max", "min", "avg")
    MAX_FIELD_NUMBER: _ClassVar[int]
    MIN_FIELD_NUMBER: _ClassVar[int]
    AVG_FIELD_NUMBER: _ClassVar[int]
    max: float
    min: float
    avg: float
    def __init__(self, max: _Optional[float] = ..., min: _Optional[float] = ..., avg: _Optional[float] = ...) -> None: ...

class PhaseVoltageReportValues(_message.Message):
    __slots__ = ("vbase", "phs1", "phs2", "phs3")
    VBASE_FIELD_NUMBER: _ClassVar[int]
    PHS1_FIELD_NUMBER: _ClassVar[int]
    PHS2_FIELD_NUMBER: _ClassVar[int]
    PHS3_FIELD_NUMBER: _ClassVar[int]
    vbase: float
    phs1: MaxMinAvg
    phs2: MaxMinAvg
    phs3: MaxMinAvg
    def __init__(self, vbase: _Optional[float] = ..., phs1: _Optional[_Union[MaxMinAvg, _Mapping]] = ..., phs2: _Optional[_Union[MaxMinAvg, _Mapping]] = ..., phs3: _Optional[_Union[MaxMinAvg, _Mapping]] = ...) -> None: ...

class PhaseVoltageReport(_message.Message):
    __slots__ = ("element", "hour", "values")
    ELEMENT_FIELD_NUMBER: _ClassVar[int]
    HOUR_FIELD_NUMBER: _ClassVar[int]
    VALUES_FIELD_NUMBER: _ClassVar[int]
    element: str
    hour: float
    values: _containers.RepeatedCompositeFieldContainer[PhaseVoltageReportValues]
    def __init__(self, element: _Optional[str] = ..., hour: _Optional[float] = ..., values: _Optional[_Iterable[_Union[PhaseVoltageReportValues, _Mapping]]] = ...) -> None: ...

class OverloadReport(_message.Message):
    __slots__ = ("hour", "element", "normalAmps", "emergAmps", "percentNormal", "percentEmerg", "kvBase", "phase1Amps", "phase2Amps", "phase3Amps")
    HOUR_FIELD_NUMBER: _ClassVar[int]
    ELEMENT_FIELD_NUMBER: _ClassVar[int]
    NORMALAMPS_FIELD_NUMBER: _ClassVar[int]
    EMERGAMPS_FIELD_NUMBER: _ClassVar[int]
    PERCENTNORMAL_FIELD_NUMBER: _ClassVar[int]
    PERCENTEMERG_FIELD_NUMBER: _ClassVar[int]
    KVBASE_FIELD_NUMBER: _ClassVar[int]
    PHASE1AMPS_FIELD_NUMBER: _ClassVar[int]
    PHASE2AMPS_FIELD_NUMBER: _ClassVar[int]
    PHASE3AMPS_FIELD_NUMBER: _ClassVar[int]
    hour: float
    element: str
    normalAmps: float
    emergAmps: float
    percentNormal: float
    percentEmerg: float
    kvBase: float
    phase1Amps: float
    phase2Amps: float
    phase3Amps: float
    def __init__(self, hour: _Optional[float] = ..., element: _Optional[str] = ..., normalAmps: _Optional[float] = ..., emergAmps: _Optional[float] = ..., percentNormal: _Optional[float] = ..., percentEmerg: _Optional[float] = ..., kvBase: _Optional[float] = ..., phase1Amps: _Optional[float] = ..., phase2Amps: _Optional[float] = ..., phase3Amps: _Optional[float] = ...) -> None: ...

class VoltageReportValues(_message.Message):
    __slots__ = ("underVoltages", "minVoltage", "overVoltage", "maxVoltage", "minBus", "maxBus")
    UNDERVOLTAGES_FIELD_NUMBER: _ClassVar[int]
    MINVOLTAGE_FIELD_NUMBER: _ClassVar[int]
    OVERVOLTAGE_FIELD_NUMBER: _ClassVar[int]
    MAXVOLTAGE_FIELD_NUMBER: _ClassVar[int]
    MINBUS_FIELD_NUMBER: _ClassVar[int]
    MAXBUS_FIELD_NUMBER: _ClassVar[int]
    underVoltages: int
    minVoltage: float
    overVoltage: int
    maxVoltage: float
    minBus: str
    maxBus: str
    def __init__(self, underVoltages: _Optional[int] = ..., minVoltage: _Optional[float] = ..., overVoltage: _Optional[int] = ..., maxVoltage: _Optional[float] = ..., minBus: _Optional[str] = ..., maxBus: _Optional[str] = ...) -> None: ...

class VoltageReport(_message.Message):
    __slots__ = ("hour", "hv", "lv")
    HOUR_FIELD_NUMBER: _ClassVar[int]
    HV_FIELD_NUMBER: _ClassVar[int]
    LV_FIELD_NUMBER: _ClassVar[int]
    hour: float
    hv: VoltageReportValues
    lv: VoltageReportValues
    def __init__(self, hour: _Optional[float] = ..., hv: _Optional[_Union[VoltageReportValues, _Mapping]] = ..., lv: _Optional[_Union[VoltageReportValues, _Mapping]] = ...) -> None: ...
