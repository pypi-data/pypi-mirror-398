__version__ = "0.1.3dev2"

from .core.csv import append_csv, read_csv, write_csv
from .core.exceptions import AppException, CriticalException
from .core.file import append_file, read_file, write_file
from .core.json import append_json, read_json, write_json
from .core.logging import LoggingManager, LoggingManagerConfig, setup_logger
from .core.os import get_dated_filename, get_files, get_folders, get_unique_filename
from .core.str import (
    anti_capitalize,
    camel_to_snake_case,
    camel_to_spaced,
    capitalize,
    clear_string,
    dstr,
    lstr,
    snake_to_camel_case,
    spaced_to_camel,
)
from .core.time import get_current_date, get_timestamp
from .core.web import get_curl
from .core.wrappers import handle_exceptions, nullable
from .pipeline.conditions import (
    AlwaysExecute,
    AndCondition,
    ConfigFlagCondition,
    CustomCondition,
    InputNotEmptyCondition,
    OrCondition,
    StageCondition,
    VariableExistsCondition,
)
from .pipeline.context import PipelineContext
from .pipeline.data_source import CSVSource, DataSource, FileSource, JSONSource
from .pipeline.definition import PipelineDefinition
from .pipeline.descriptors import sconsume, sproduce, stransform
from .pipeline.memory import MemoryConfig, MemoryManager, MemoryTracker, VariableMemoryInfo
from .pipeline.pipeline_metadata import PipelineMetadata
from .pipeline.runner import PipelineRunner
from .pipeline.stages import ETLStage
from .pipeline.variables import DFVar, NDArrayVar, SVar

__all__ = [
    "__version__",
    "append_csv",
    "read_csv",
    "write_csv",
    "AppException",
    "CriticalException",
    "append_file",
    "read_file",
    "write_file",
    "append_json",
    "read_json",
    "write_json",
    "LoggingManager",
    "LoggingManagerConfig",
    "setup_logger",
    "get_dated_filename",
    "get_files",
    "get_folders",
    "get_unique_filename",
    "anti_capitalize",
    "camel_to_snake_case",
    "camel_to_spaced",
    "capitalize",
    "clear_string",
    "dstr",
    "lstr",
    "snake_to_camel_case",
    "spaced_to_camel",
    "get_current_date",
    "get_timestamp",
    "handle_exceptions",
    "nullable",
    "get_curl",
    "CSVSource",
    "DataSource",
    "FileSource",
    "JSONSource",
    "PipelineContext",
    "PipelineDefinition",
    "PipelineMetadata",
    "PipelineRunner",
    "ETLStage",
    "DFVar",
    "NDArrayVar",
    "SVar",
    "sconsume",
    "sproduce",
    "stransform",
    "MemoryConfig",
    "MemoryManager",
    "MemoryTracker",
    "VariableMemoryInfo",
    "StageCondition",
    "AlwaysExecute",
    "InputNotEmptyCondition",
    "ConfigFlagCondition",
    "VariableExistsCondition",
    "CustomCondition",
    "AndCondition",
    "OrCondition",
]
