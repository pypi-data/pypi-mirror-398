from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class Syf(_message.Message):
    __slots__ = ("scenario", "year", "feeder", "commonConfig", "generatorConfig", "executorConfig", "resultProcessorConfig", "auxiliaryData", "interventionConfig")
    SCENARIO_FIELD_NUMBER: _ClassVar[int]
    YEAR_FIELD_NUMBER: _ClassVar[int]
    FEEDER_FIELD_NUMBER: _ClassVar[int]
    COMMONCONFIG_FIELD_NUMBER: _ClassVar[int]
    GENERATORCONFIG_FIELD_NUMBER: _ClassVar[int]
    EXECUTORCONFIG_FIELD_NUMBER: _ClassVar[int]
    RESULTPROCESSORCONFIG_FIELD_NUMBER: _ClassVar[int]
    AUXILIARYDATA_FIELD_NUMBER: _ClassVar[int]
    INTERVENTIONCONFIG_FIELD_NUMBER: _ClassVar[int]
    scenario: str
    year: int
    feeder: str
    commonConfig: str
    generatorConfig: str
    executorConfig: str
    resultProcessorConfig: str
    auxiliaryData: str
    interventionConfig: str
    def __init__(self, scenario: _Optional[str] = ..., year: _Optional[int] = ..., feeder: _Optional[str] = ..., commonConfig: _Optional[str] = ..., generatorConfig: _Optional[str] = ..., executorConfig: _Optional[str] = ..., resultProcessorConfig: _Optional[str] = ..., auxiliaryData: _Optional[str] = ..., interventionConfig: _Optional[str] = ...) -> None: ...
