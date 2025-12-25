from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class Job(_message.Message):
    __slots__ = ("feeder", "scenarios", "years", "commonConfig", "generatorConfig", "executorConfig", "resultProcessorConfig", "interventionConfig")
    FEEDER_FIELD_NUMBER: _ClassVar[int]
    SCENARIOS_FIELD_NUMBER: _ClassVar[int]
    YEARS_FIELD_NUMBER: _ClassVar[int]
    COMMONCONFIG_FIELD_NUMBER: _ClassVar[int]
    GENERATORCONFIG_FIELD_NUMBER: _ClassVar[int]
    EXECUTORCONFIG_FIELD_NUMBER: _ClassVar[int]
    RESULTPROCESSORCONFIG_FIELD_NUMBER: _ClassVar[int]
    INTERVENTIONCONFIG_FIELD_NUMBER: _ClassVar[int]
    feeder: str
    scenarios: _containers.RepeatedScalarFieldContainer[str]
    years: _containers.RepeatedScalarFieldContainer[int]
    commonConfig: str
    generatorConfig: str
    executorConfig: str
    resultProcessorConfig: str
    interventionConfig: str
    def __init__(self, feeder: _Optional[str] = ..., scenarios: _Optional[_Iterable[str]] = ..., years: _Optional[_Iterable[int]] = ..., commonConfig: _Optional[str] = ..., generatorConfig: _Optional[str] = ..., executorConfig: _Optional[str] = ..., resultProcessorConfig: _Optional[str] = ..., interventionConfig: _Optional[str] = ...) -> None: ...
