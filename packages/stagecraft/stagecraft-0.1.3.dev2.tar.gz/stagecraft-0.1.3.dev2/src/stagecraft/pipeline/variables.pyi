from typing import Callable, Generic, Iterable, List, Optional, Type, TypeVar, overload

import numpy as np
import pandera.pandas as pa
from pandera.typing import DataFrame

from .context import PipelineContext
from .data_source import ArraySource, CSVSource, DataSource
from .markers import IOMarker

_T = TypeVar("_T")
_SCHEMA = TypeVar("_SCHEMA", bound=pa.DataFrameModel)

class SVar(Generic[_T]):
    name: str
    context: PipelineContext
    value: Optional[_T]

    factory: Optional[Callable[[], _T]]
    default: Optional[_T]
    source: Optional[DataSource]
    description: Optional[str]
    pre_processing: Optional[Callable[[_T], _T]]
    markers: Optional[List[IOMarker]]

    @overload
    def __init__(
        self,
        type_: Optional[Type[_T]] = None,
        /,
        *,
        factory: Callable[[], _T],
        source: Optional[DataSource] = None,
        description: Optional[str] = None,
        pre_processing: Optional[Callable[[_T], _T]] = None,
        markers: Optional[List[IOMarker]] = None,
    ) -> None: ...
    @overload
    def __init__(
        self,
        type_: Optional[Type[_T]] = None,
        /,
        *,
        default: _T,
        source: Optional[DataSource] = None,
        description: Optional[str] = None,
        pre_processing: Optional[Callable[[_T], _T]] = None,
        markers: Optional[List[IOMarker]] = None,
    ) -> None: ...
    @overload
    def __init__(
        self,
        type_: Type[_T],
        /,
        *,
        source: Optional[DataSource] = None,
        description: Optional[str] = None,
        pre_processing: Optional[Callable[[_T], _T]] = None,
        markers: Optional[List[IOMarker]] = None,
    ) -> None: ...
    @overload
    def __init__(
        self,
        *,
        source: Optional[DataSource] = None,
        description: Optional[str] = None,
        pre_processing: Optional[Callable[[_T], _T]] = None,
        markers: Optional[List[IOMarker]] = None,
    ) -> None: ...
    def set_markers(self, markers: List[IOMarker]) -> None: ...
    def set_context(self, context: PipelineContext) -> None: ...
    def load(self) -> None: ...
    def save(self) -> None: ...
    def get(self) -> _T: ...
    def set(self, value: _T) -> None: ...
    def delete(self) -> None: ...
    def validate(self) -> bool: ...
    def sconsume(self) -> _T: ...
    def sproduce(self) -> _T: ...
    def stransform(self) -> _T: ...

class DFVar(Generic[_SCHEMA], SVar[DataFrame[_SCHEMA]]):
    schema: Optional[_SCHEMA]

    @overload
    def __init__(
        self,
        schema: Optional[Type[_SCHEMA]] = None,
        /,
        *,
        factory: Callable[[], DataFrame[_SCHEMA]],
        source: Optional[CSVSource] = None,
        description: Optional[str] = None,
        pre_processing: Optional[Callable[[DataFrame[_SCHEMA]], DataFrame[_SCHEMA]]] = None,
        markers: Optional[List[IOMarker]] = None,
    ) -> None: ...
    @overload
    def __init__(
        self,
        schema: Optional[Type[_SCHEMA]] = None,
        /,
        *,
        default: DataFrame[_SCHEMA],
        source: Optional[CSVSource] = None,
        description: Optional[str] = None,
        pre_processing: Optional[Callable[[DataFrame[_SCHEMA]], DataFrame[_SCHEMA]]] = None,
        markers: Optional[List[IOMarker]] = None,
    ) -> None: ...
    @overload
    def __init__(
        self,
        schema: Type[_SCHEMA],
        /,
        *,
        source: Optional[CSVSource] = None,
        description: Optional[str] = None,
        pre_processing: Optional[Callable[[DataFrame[_SCHEMA]], DataFrame[_SCHEMA]]] = None,
        markers: Optional[List[IOMarker]] = None,
    ) -> None: ...
    @overload
    def __init__(
        self,
        *,
        source: Optional[CSVSource] = None,
        description: Optional[str] = None,
        pre_processing: Optional[Callable[[DataFrame[_SCHEMA]], DataFrame[_SCHEMA]]] = None,
        markers: Optional[List[IOMarker]] = None,
    ) -> None: ...
    @property
    def columns(self) -> Optional[List[str]]: ...
    def iter_chunks(self, chunk_size: int) -> Iterable[DataFrame[_SCHEMA]]: ...
    def process_in_chunks(
        self, chunk_size: int, process_fn: Callable[[DataFrame[_SCHEMA]], DataFrame[_SCHEMA]]
    ) -> Optional[DataFrame[_SCHEMA]]: ...

class NDArrayVar(Generic[_T], SVar[np.ndarray]):
    shape: Optional[tuple]

    @overload
    def __init__(
        self,
        *,
        factory: Callable[[], np.ndarray],
        source: Optional[ArraySource] = None,
        description: Optional[str] = None,
        pre_processing: Optional[Callable[[np.ndarray], np.ndarray]] = None,
        shape: Optional[tuple] = None,
        markers: Optional[List[IOMarker]] = None,
    ) -> None: ...
    @overload
    def __init__(
        self,
        *,
        default: np.ndarray,
        source: Optional[ArraySource] = None,
        description: Optional[str] = None,
        pre_processing: Optional[Callable[[np.ndarray], np.ndarray]] = None,
        shape: Optional[tuple] = None,
        markers: Optional[List[IOMarker]] = None,
    ) -> None: ...
    @overload
    def __init__(
        self,
        *,
        source: Optional[ArraySource] = None,
        description: Optional[str] = None,
        pre_processing: Optional[Callable[[np.ndarray], np.ndarray]] = None,
        shape: Optional[tuple] = None,
        markers: Optional[List[IOMarker]] = None,
    ) -> None: ...
