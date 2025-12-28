from datetime import datetime
from enum import Enum
from typing import Any, List, Optional

from pydantic import Field

from ..core.exceptions import AppException
from ..core.serializable import Serializable


class ExecutionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class StageExecutionMetadata(Serializable):
    name: str
    duration: Optional[float] = None
    status: ExecutionStatus = ExecutionStatus.PENDING
    error: Optional[Exception] = None

    def __post_init__(self):
        if not isinstance(self.error, AppException):
            self.error = AppException(self.error, self.__class__.__name__)


class PipelineExecutionMetadata(Serializable):
    pipeline_name: str
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    stages_executed: List[StageExecutionMetadata] = Field(default_factory=list)
    status: ExecutionStatus = ExecutionStatus.PENDING
    error: Optional[Exception] = None

    def __post_init__(self):
        if not isinstance(self.error, AppException):
            self.error = AppException(self.error, self.__class__.__name__)


class StageParameter(Serializable):
    name: str
    value: Any
    description: Optional[str] = None


class StageMetadata(Serializable):
    name: str
    parameters: List[StageParameter] = Field(default_factory=list)


class PipelineMetadata(Serializable):
    name: str
    stages: List[StageMetadata] = Field(default_factory=list)


class PipelineResult(Serializable):
    success: bool
    metadata: Optional[PipelineExecutionMetadata] = None
    error: Optional[Exception] = None

    def __post_init__(self):
        if not isinstance(self.error, AppException):
            self.error = AppException(self.error, self.__class__.__name__)
