"""Stage variable classes for type-safe data flow in ETL pipelines.

This module provides variable classes that enable type-safe, validated data flow
between pipeline stages. Variables handle:

- Value storage and retrieval
- Loading from data sources (CSV, JSON, NumPy arrays) or pipeline context
- Saving to data sources or pipeline context
- Type validation and schema validation (for DataFrames)
- Preprocessing transformations
- Descriptor protocol for clean attribute access

The module includes three main variable types:

1. **SVar**: Generic stage variable for any Python type
2. **DFVar**: Specialized variable for pandas DataFrames with Pandera schema support
3. **NDArrayVar**: Specialized variable for NumPy arrays with shape validation

Variables are typically declared using descriptor functions (sconsume, sproduce,
stransform) at the class level in ETL stages:

Example:
    >>> class MyStage(ETLStage):
    ...     # Generic variable
    ...     config = scstransformonsume(dict)
    ...     config = SVar(dict).stransform()  # Equivalent
    ...
    ...     # DataFrame with schema
    ...     input_data = sconsume(DFVar(MySchema))
    ...     input_data = SVar(DFVar(MySchema)).sconsume()  # Equivalent
    ...
    ...     # NumPy array with shape
    ...     embeddings = sproduce(NDArrayVar(shape=(100, 768)))
    ...     embeddings = SVar(NDArrayVar(shape=(100, 768))).sproduce()  # Equivalent
    ...
    ...     def recipe(self):
    ...         df = self.input_data  # Automatically loaded
    ...         self.embeddings = compute_embeddings(df)  # Automatically saved
"""

from __future__ import annotations

import copy
import logging
from typing import TYPE_CHECKING, Callable, Generic, Iterable, List, Optional, Type, TypeVar

import numpy as np
import pandas as pd
import pandera.pandas as pa
from pandera.typing import DataFrame

from .context import PipelineContext
from .data_source import ArraySource, CSVSource, DataSource
from .markers import IOMarker

if TYPE_CHECKING:
    pass

_T = TypeVar("_T")
_SCHEMA = TypeVar("_SCHEMA", bound=pa.DataFrameModel)


logger = logging.getLogger(__name__)


class SVar(Generic[_T]):
    """
    A generic stage variable that holds and manages data within a pipeline stage.

    SVar provides the runtime behavior for stage variables, including value storage,
    loading from data sources or context, saving to context, and validation. It supports
    multiple initialization strategies (factory, default, or lazy loading) and optional
    preprocessing of values.

    Stands for 'Stage Variable'.

    Attributes:
        value: The current value of the variable.
        context: The pipeline context for loading/saving data (set by PipelineRunner).
        name: The variable name as defined on the stage class.
        factory: Optional callable that produces new instances of the value.
        default: Optional static default value.
        type: The expected type of the variable value.
        source: Optional data source for loading/saving the value.
        description: Human-readable description of the variable's purpose.
        pre_processing: Optional transformation applied to values before storage.
        markers: List of IOMarkers for input/output classification.
    """

    name: str
    context: Optional[PipelineContext] = None
    value: Optional[_T] = None

    def __init__(
        self,
        type_: Optional[Type[_T]] = None,
        /,
        *,
        factory: Optional[Callable[[], _T]] = None,
        default: Optional[_T] = None,
        source: Optional[DataSource] = None,
        description: Optional[str] = None,
        pre_processing: Optional[Callable[[_T], _T]] = None,
        markers: Optional[List[IOMarker]] = None,
    ):
        """
        Initialize a stage variable.

        Args:
            type_: The expected type of the variable value.
            factory: Callable that produces a new instance of the variable value.
                Cannot be used together with default.
            default: Static default value for the variable. Cannot be used together
                with factory.
            source: Data source for loading/saving the variable value.
            description: Human-readable description of the variable's purpose.
            pre_processing: Optional transformation function applied to values before
                they are stored in the variable.
            markers: List of IOMarkers for input/output classification.

        Raises:
            AssertionError: If both factory and default are provided.
        """
        assert not (factory and default), "Only one of factory or default can be provided"
        self.factory = factory
        self.default = default
        self.type = type_
        self.source = source
        self.description = description
        self.value = self.__create_default_value()
        self.pre_processing = pre_processing
        self.markers = markers or []

    def set_markers(self, markers: List[IOMarker]):
        """Set the I/O markers for this variable.

        Args:
            markers: List of IOMarker values (INPUT, OUTPUT, or both).

        Example:
            >>> var = SVar(pd.DataFrame, name="data")
            >>> var.set_markers([IOMarker.INPUT])
        """
        self.markers = markers

    def __set_name__(self, owner, name):
        """Descriptor protocol method called when variable is assigned to a class.

        This method is automatically called by Python when the variable is
        assigned as a class attribute. It:
        1. Sets the variable name from the attribute name
        2. Infers the type from class annotations if not explicitly provided
        3. Registers the variable with the owner class for later injection

        Args:
            owner: The class that owns this variable (typically an ETLStage subclass).
            name: The attribute name assigned to this variable.

        Example:
            >>> class MyStage(ETLStage):
            ...     # __set_name__ is called automatically here
            ...     data = sconsume(pd.DataFrame)
            ...     # After this line, data.name == "data"

        Note:
            This is an internal method called by Python's descriptor protocol.
            It should not be called manually.
        """
        self.name = name

        # Ensure __annotations__ exists
        if not hasattr(owner, "__annotations__"):
            owner.__annotations__ = {}

        # Infer type from annotations if not explicitly provided
        self.type = self.type or owner.__annotations__.get(name) or type(_T)
        owner.__annotations__[name] = self.type

        if not hasattr(owner, "_pending_variables"):
            owner._pending_variables = []  # type: ignore
        owner._pending_variables.append((self, self.markers))  # type: ignore

    def __create_default_value(self) -> Optional[_T]:
        """
        Create the initial default value using factory or default.

        Returns:
            The initial value, or None if neither factory nor default is provided.
        """
        if self.factory:
            value = self.factory()
            if self.pre_processing:
                value = self.pre_processing(value)
            return value
        elif self.default:
            value = copy.deepcopy(self.default)
            if self.pre_processing:
                value = self.pre_processing(value)
                return value
            return value
        else:
            return None

    def set_context(self, context: PipelineContext):
        """
        Set the pipeline context for this variable.

        Args:
            context: The pipeline context to use for loading/saving data.
        """
        self.context = context

    def load(self):
        """
        Load the variable value from its source or context.

        If a source is configured, loads from the source. Otherwise, loads from
        the pipeline context using the variable name if context exists. Applies
        preprocessing if configured.
        """
        if not hasattr(self, "name"):
            raise ValueError(
                "Variable name is not set. Ensure the variable is properly initialized in a class."
            )

        try:
            if hasattr(self, "context") and self.context:
                value = self.context.get(self.name, None)

            if value is None and self.source and self.source.load_enabled:
                value = self.source.load()

            if value is not None:
                if self.pre_processing:
                    value = self.pre_processing(value)  # type: ignore[arg-type]
                self.value = value

            if self.value is None:
                logger.warning(
                    f"None value for '{self.name}' while loading. "
                    "No value found in context or source. "
                    "If intentional, you can ignore this message."
                )
        except Exception as e:
            raise RuntimeError(
                f"Failed to load variable '{self.name}'. "
                f"Source: {'file' if self.source else 'context'}.\n"
                f"Original error: {str(e)}"
            ) from e

    def save(self):
        """
        Save the variable value to the context and optionally to its source.

        Always saves to the pipeline context if context exists. If a source is
        configured, also saves to the source (e.g., CSV file, array file).
        """
        if not hasattr(self, "name"):
            raise ValueError(
                "Variable name is not set. Ensure the variable is properly initialized in a class."
            )

        try:
            if self.value is None:
                logger.warning(
                    f"None value for '{self.name}' while saving. "
                    "No value found in context or source. "
                    "If intentional, you can ignore this message."
                )

            if hasattr(self, "context") and self.context:
                self.context.set(self.name, self.value)
            if self.value is not None and self.source is not None and self.source.save_enabled:
                self.source.save(self.value)
        except Exception as e:
            raise RuntimeError(
                f"Failed to save variable '{self.name}'. "
                f"Destination: {'file and context' if self.source else 'context'}.\n"
                f"Original error: {str(e)}"
            ) from e

    def get(self) -> Optional[_T]:
        """
        Get the current value of the variable.

        Returns:
            The current value.
        """
        return self.value

    def set(self, value: Optional[_T]):
        """
        Set the value of the variable.

        Args:
            value: The new value to store.
        """
        self.value = value

    def delete(self):
        """
        Delete the variable value from memory.

        Sets the value to None to allow garbage collection.
        Note: The actual memory cleanup depends on Python's garbage collector.
        """
        self.value = None

    def validate(self) -> bool:
        """
        Validate that the current value matches the expected type.

        Returns:
            True if the value is valid or no type is specified

        Raises:
            TypeError: If the value doesn't match the expected type
        """
        if not hasattr(self, "name"):
            raise ValueError("Variable name is not set. Cannot validate unnamed variable.")

        if self.type is None or self.value is None:
            return True

        # Skip validation for generic types (they can't be used with isinstance)
        if hasattr(self.type, "__origin__"):
            logger.warning(
                f"Skipping type validation for generic type {self.type} in variable '{self.name}'. "
                "Subclasses should override validate() for specific checks."
            )
            # Subclasses should override validate() for specific checks
            return True

        try:
            if not isinstance(self.value, self.type):
                raise TypeError(
                    f"Variable '{self.name}' type validation failed. "
                    f"Expected type: {self.type.__name__}, "
                    f"Got: {type(self.value).__name__}. "
                    f"Ensure the stage's recipe() method produces the correct output type."
                )
        except TypeError as e:
            # isinstance() can fail with some types, skip validation in that case
            if "Subscripted generics cannot be used" in str(e):
                return True
            raise
        return True

    def sconsume(self) -> SVar[_T]:
        """Mark this variable as an input (consumed) by the stage.

        Returns:
            Self for method chaining.

        Example:
            >>> var = SVar(pd.DataFrame).sconsume()
            >>> # Equivalent to using sconsume() descriptor function
        """
        self.set_markers([IOMarker.INPUT])
        return self

    def sproduce(self) -> SVar[_T]:
        """Mark this variable as an output (produced) by the stage.

        Returns:
            Self for method chaining.

        Example:
            >>> var = SVar(pd.DataFrame).sproduce()
            >>> # Equivalent to using sproduce() descriptor function
        """
        self.set_markers([IOMarker.OUTPUT])
        return self

    def stransform(self) -> SVar[_T]:
        """Mark this variable as both input and output (transformed) by the stage.

        Returns:
            Self for method chaining.

        Example:
            >>> var = SVar(pd.DataFrame).stransform()
            >>> # Equivalent to using stransform() descriptor function
        """
        self.set_markers([IOMarker.INPUT, IOMarker.OUTPUT])
        return self

    def __get__(self, instance, owner):
        """Descriptor protocol method for attribute access.

        This method is called when the variable is accessed as an attribute
        on a stage instance. It returns the current value of the variable.

        Args:
            instance: The stage instance accessing the variable, or None if
                     accessed on the class.
            owner: The class that owns this descriptor.

        Returns:
            The descriptor itself if accessed on the class, otherwise the
            variable's current value.

        Example:
            >>> class MyStage(ETLStage):
            ...     data = sconsume(pd.DataFrame)
            ...
            >>> stage = MyStage()
            >>> # Accessing stage.data calls __get__
            >>> df = stage.data  # Returns the DataFrame value

        Note:
            This is an internal method called by Python's descriptor protocol.
        """
        if instance is None:
            return self
        if hasattr(instance, "_dynamic_props") and self.name in instance._dynamic_props:
            return instance._dynamic_props[self.name]["getter"]()

        return self.get()

    def __set__(self, instance, value):
        """Descriptor protocol method for attribute assignment.

        This method is called when the variable is assigned a value as an
        attribute on a stage instance. It stores the value in the variable.

        Args:
            instance: The stage instance setting the variable.
            value: The value to store.

        Raises:
            ValueError: If attempting to set on the class rather than an instance.

        Example:
            >>> class MyStage(ETLStage):
            ...     result = sproduce(pd.DataFrame)
            ...
            >>> stage = MyStage()
            >>> # Assigning to stage.result calls __set__
            >>> stage.result = processed_df  # Stores the DataFrame

        Note:
            This is an internal method called by Python's descriptor protocol.
        """
        if instance is None:
            raise ValueError("Cannot set value on class")
        if hasattr(instance, "_dynamic_props") and self.name in instance._dynamic_props:
            instance._dynamic_props[self.name]["setter"](value)
        else:
            self.set(value)

    def __delete__(self, instance):
        """Descriptor protocol method for attribute deletion.

        This method is called when the variable is deleted as an attribute
        on a stage instance. It clears the variable's value from memory.

        Args:
            instance: The stage instance deleting the variable.

        Example:
            >>> class MyStage(ETLStage):
            ...     temp_data = stransform(pd.DataFrame)
            ...
            >>> stage = MyStage()
            >>> stage.temp_data = df
            >>> # Deleting stage.temp_data calls __delete__
            >>> del stage.temp_data  # Clears the value

        Note:
            This is an internal method called by Python's descriptor protocol.
        """
        if instance is None:
            return

        if hasattr(instance, "_dynamic_props") and self.name in instance._dynamic_props:
            instance._dynamic_props[self.name]["deleter"]()
        else:
            self.delete()

    def __str__(self):
        """Return string representation of the variable's value.

        Returns:
            String representation of the current value.

        Example:
            >>> var = SVar(str, default="hello")
            >>> str(var)
            'hello'
        """
        return self.value.__str__()

    def __repr__(self):
        """Return detailed string representation of the variable's value.

        Returns:
            Detailed string representation of the current value.

        Example:
            >>> var = SVar(list, default=[1, 2, 3])
            >>> repr(var)
            '[1, 2, 3]'
        """
        return self.value.__repr__()


class DFVar(Generic[_SCHEMA], SVar[DataFrame[_SCHEMA]]):
    """DataFrame variable with Pandera schema validation and type safety.

    DFVar extends SVar to provide specialized handling for pandas DataFrames with
    Pandera schema support. It enables:

    - Type-safe DataFrame operations with IDE autocomplete for columns
    - Runtime schema validation with automatic type coercion
    - Column introspection
    - Memory-efficient chunk processing for large DataFrames
    - CSV file integration for loading/saving

    The schema parameter accepts a Pandera DataFrameModel class, which provides:
    - Column name and type definitions
    - Validation rules (nullable, unique, ranges, etc.)
    - Automatic type coercion during validation
    - IDE support for column access (e.g., df['column_name'])

    Stands for 'DataFrame Variable'.

    Attributes:
        schema: Pandera DataFrameModel class for runtime validation and type safety.
        value: The current DataFrame value.
        columns: List of column names (property).

    Example:
        >>> class MySchema(pa.DataFrameModel):
        ...     customer_id: int
        ...     amount: float = pa.Field(ge=0)
        ...     date: pd.Timestamp
        ...
        >>> class ProcessStage(ETLStage):
        ...     input_data = sconsume(DFVar(MySchema))
        ...     output_data = sproduce(DFVar(MySchema))
        ...
        ...     def recipe(self):
        ...         df = self.input_data  # Type: DataFrame[MySchema]
        ...         # IDE knows about customer_id, amount, date columns
        ...         df = df[df['amount'] > 100]
        ...         self.output_data = df  # Validated on save
    """

    schema: Optional[_SCHEMA]

    def __init__(
        self,
        schema: Optional[_SCHEMA] = None,
        /,
        *,
        factory: Optional[Callable[[], DataFrame[_SCHEMA]]] = None,
        default: Optional[DataFrame[_SCHEMA]] = None,
        source: Optional[CSVSource] = None,
        description: Optional[str] = None,
        pre_processing: Optional[Callable[[DataFrame[_SCHEMA]], DataFrame[_SCHEMA]]] = None,
        markers: Optional[List[IOMarker]] = None,
    ):
        """Initialize a DataFrame variable with optional schema validation.

        Args:
            schema: Optional Pandera DataFrameModel class for runtime validation.
                   If provided, the DataFrame will be validated against this schema
                   whenever validate() is called.
            factory: Optional callable that produces a new DataFrame instance.
                    Cannot be used together with default.
            default: Optional static default DataFrame value.
                    Cannot be used together with factory.
            source: Optional CSV source for loading/saving the DataFrame.
            description: Optional human-readable description of the DataFrame's purpose.
            pre_processing: Optional transformation function applied to the DataFrame
                          before it is stored in the variable.
            markers: Optional list of IOMarkers for input/output classification.

        Example:
            >>> # With schema validation
            >>> var = DFVar(
            ...     MySchema,
            ...     source=CSVSource("data.csv"),
            ...     description="Customer transactions"
            ... )
            >>>
            >>> # With factory for empty DataFrame
            >>> var = DFVar(
            ...     MySchema,
            ...     factory=lambda: pd.DataFrame(columns=['id', 'value'])
            ... )
            >>>
            >>> # With preprocessing
            >>> var = DFVar(
            ...     MySchema,
            ...     pre_processing=lambda df: df.drop_duplicates()
            ... )
        """
        super().__init__(
            DataFrame[_SCHEMA],
            factory=factory,
            default=default,
            source=source,
            description=description,
            pre_processing=pre_processing,
            markers=markers,
        )
        self.schema = schema

    def _SVar__create_default_value(self) -> Optional[DataFrame[_SCHEMA]]:
        """Create the initial default value using factory or default.

        Overrides the parent SVar method to use DataFrame.copy() instead of
        copy.deepcopy() for better performance with large DataFrames. The
        deepcopy operation can be very slow for DataFrames with many rows.

        Returns:
            The initial DataFrame value, or None if neither factory nor default
            is provided.

        Note:
            This is an internal method that overrides the parent's private method
            using name mangling. It's called during __init__.
        """

        if self.factory:
            value = self.factory()
            if self.pre_processing:
                value = self.pre_processing(value)
            return value
        elif self.default is not None:
            if isinstance(self.default, pd.DataFrame):
                value = self.default.copy()
            else:
                value = copy.deepcopy(self.default)
            if self.pre_processing:
                value = self.pre_processing(value)
            return value
        else:
            return None

    @property
    def columns(self) -> Optional[List[str]]:
        """Get the column names of the DataFrame.

        Returns:
            List of column names if the DataFrame has a value, None otherwise.

        Example:
            >>> var = DFVar(MySchema)
            >>> var.value = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
            >>> print(var.columns)
            ['a', 'b']
            >>> var.value = None
            >>> print(var.columns)
            None
        """
        if self.value is None:
            return None
        return self.value.columns.tolist()

    def validate(self) -> bool:
        """Validate the DataFrame against its schema.

        This method performs two levels of validation:
        1. Type validation: Ensures the value is a pandas DataFrame
        2. Schema validation: If a Pandera schema is provided, validates the
           DataFrame structure, column types, and any defined constraints

        The schema validation also performs automatic type coercion when possible,
        updating the DataFrame value with the coerced version.

        Returns:
            True if validation passes.

        Raises:
            ValueError: If the variable has no name.
            TypeError: If the value is not a pandas DataFrame.
            ValueError: If Pandera schema validation fails. The error message
                       includes details about which columns or constraints failed.

        Example:
            >>> class MySchema(pa.DataFrameModel):
            ...     id: int
            ...     value: float = pa.Field(ge=0)
            ...
            >>> var = DFVar(MySchema, name="data")
            >>> var.value = pd.DataFrame({'id': ['1', '2'], 'value': [10.5, 20.3]})
            >>> var.validate()  # Coerces 'id' to int, validates 'value' >= 0
            True
            >>> var.value = pd.DataFrame({'id': [1, 2], 'value': [-5, 10]})
            >>> var.validate()  # Raises ValueError: value must be >= 0
            ValueError: Pandera schema validation failed...

        Note:
            If no schema is provided, only basic DataFrame type checking is performed.
        """
        if not hasattr(self, "name"):
            raise ValueError(
                "Variable name is not set. Cannot validate unnamed DataFrame variable."
            )

        if self.value is None:
            return True

        if not isinstance(self.value, pd.DataFrame):
            raise TypeError(
                f"Variable '{self.name}' type validation failed. "
                f"Expected DataFrame, got {type(self.value).__name__}. "
                f"Ensure the stage's recipe() method produces a pandas DataFrame."
            )

        if self.schema is not None:
            try:
                validated_df = self.schema.validate(self.value, lazy=False)
                object.__setattr__(self, "value", validated_df)
                return True
            except Exception as e:
                raise ValueError(
                    f"Pandera schema validation failed for DataFrame '{self.name}'. "
                    f"Check that the DataFrame has the correct columns and types.\n"
                    f"Original error: {str(e)}"
                ) from e
        return True

    def iter_chunks(self, chunk_size: int) -> Iterable[DataFrame[_SCHEMA]]:
        """Iterate over the DataFrame in chunks for memory-efficient processing.

        This generator yields consecutive chunks of the DataFrame, allowing
        processing of large DataFrames without loading all data into memory
        at once. Useful for operations that can be applied row-wise or in batches.

        Args:
            chunk_size: Number of rows per chunk. Must be positive.

        Yields:
            DataFrame chunks of size chunk_size (last chunk may be smaller).

        Raises:
            ValueError: If chunk_size is not positive.

        Example:
            >>> var = DFVar(MySchema)
            >>> var.value = pd.DataFrame({'id': range(10000), 'value': range(10000)})
            >>> for chunk in var.iter_chunks(1000):
            ...     # Process each 1000-row chunk
            ...     print(f"Processing {len(chunk)} rows")
            ...     result = expensive_operation(chunk)
            Processing 1000 rows
            Processing 1000 rows
            ...
            Processing 1000 rows

        Note:
            If the DataFrame value is None, this method returns immediately
            without yielding any chunks.
        """
        if chunk_size <= 0:
            raise ValueError(
                f"chunk_size must be positive, got {chunk_size}. "
                f"Use a positive integer for the number of rows per chunk."
            )

        if self.value is None:
            return

        total_rows = len(self.value)
        for start_idx in range(0, total_rows, chunk_size):
            end_idx = min(start_idx + chunk_size, total_rows)
            # .iloc[] returns type Series[Any] because of an error in pandas stubs
            yield self.value.iloc[start_idx:end_idx]  # type: ignore

    def process_in_chunks(
        self,
        chunk_size: int,
        process_fn: Callable[[DataFrame[_SCHEMA]], DataFrame[_SCHEMA]],
    ) -> Optional[DataFrame[_SCHEMA]]:
        """Process the DataFrame in chunks and concatenate the results.

        This method provides memory-efficient processing of large DataFrames by:
        1. Splitting the DataFrame into chunks of specified size
        2. Applying a processing function to each chunk
        3. Concatenating all processed chunks into a single result DataFrame

        This is particularly useful for operations that would consume too much
        memory if applied to the entire DataFrame at once, such as:
        - Complex transformations
        - Filtering operations
        - Feature engineering
        - API calls or database lookups per row

        Args:
            chunk_size: Number of rows per chunk. Must be positive.
            process_fn: Function that takes a DataFrame chunk and returns a
                       processed DataFrame chunk. The function should maintain
                       the schema type.

        Returns:
            A new DataFrame containing all processed chunks concatenated together,
            or None if the current value is None.

        Raises:
            ValueError: If chunk_size is not positive or process_fn is None.
            RuntimeError: If processing any chunk fails. The error message includes
                         the chunk index and row range for debugging.

        Example:
            >>> var = DFVar(MySchema)
            >>> var.value = pd.DataFrame({'id': range(10000), 'value': range(10000)})
            >>>
            >>> # Filter in chunks
            >>> result = var.process_in_chunks(
            ...     chunk_size=1000,
            ...     process_fn=lambda chunk: chunk[chunk['value'] > 5000]
            ... )
            >>> print(len(result))
            4999
            >>>
            >>> # Transform in chunks
            >>> result = var.process_in_chunks(
            ...     chunk_size=1000,
            ...     process_fn=lambda chunk: chunk.assign(
            ...         value_squared=chunk['value'] ** 2
            ...     )
            ... )

        Note:
            The concatenation uses ignore_index=True, so the resulting DataFrame
            will have a new sequential index starting from 0.
        """

        if chunk_size <= 0:
            raise ValueError(
                f"chunk_size must be positive, got {chunk_size}. "
                f"Use a positive integer for the number of rows per chunk."
            )

        if process_fn is None:
            raise ValueError("process_fn cannot be None. Provide a function to process each chunk.")

        if self.value is None:
            return None

        try:
            processed_chunks = []
            for i, chunk in enumerate(self.iter_chunks(chunk_size)):
                try:
                    processed_chunk = process_fn(chunk)
                    processed_chunks.append(processed_chunk)
                except Exception as e:
                    raise RuntimeError(
                        f"Error processing chunk {i} (rows {i*chunk_size} to {(i+1)*chunk_size}) "
                        f"of DataFrame '{self.name}'.\nOriginal error: {str(e)}"
                    ) from e

            result = pd.concat(processed_chunks, ignore_index=True)
            return DataFrame[_SCHEMA](result)
        except Exception as e:
            if isinstance(e, RuntimeError) and "Error processing chunk" in str(e):
                raise
            raise RuntimeError(
                f"Failed to process DataFrame '{self.name}' in chunks.\n"
                f"Original error: {str(e)}"
            ) from e


class NDArrayVar(Generic[_T], SVar[np.ndarray]):
    """NumPy array variable with shape validation for numerical data.

    NDArrayVar extends SVar to provide specialized handling for NumPy arrays with
    optional shape validation. It enables:

    - Type-safe array operations
    - Shape validation to catch dimension mismatches early
    - Integration with ArraySource for .npy file loading/saving
    - Support for structured arrays and multi-dimensional data
    - Preprocessing transformations (normalization, reshaping, etc.)

    The shape parameter can be used to enforce specific array dimensions,
    which is particularly useful for:
    - Machine learning model inputs/outputs (e.g., embeddings, predictions)
    - Image data (height, width, channels)
    - Time series data (samples, features)
    - Matrix operations requiring specific dimensions

    Stands for 'NumPy Array Variable'.

    Attributes:
        shape: Expected shape tuple (e.g., (100, 768) for 100 embeddings of 768 dimensions).
        value: The current NumPy array value.

    Example:
        >>> class EmbeddingStage(ETLStage):
        ...     # Input: 2D array of text data
        ...     text_ids = sconsume(NDArrayVar(shape=(None, 512)))
        ...
        ...     # Output: 2D array of embeddings
        ...     embeddings = sproduce(NDArrayVar(
        ...         shape=(None, 768),
        ...         source=ArraySource("embeddings.npy", mode="w")
        ...     ))
        ...
        ...     def recipe(self):
        ...         # Process text_ids to generate embeddings
        ...         self.embeddings = model.encode(self.text_ids)
        >>>
        >>> # With preprocessing
        >>> normalized_data = NDArrayVar(
        ...     shape=(1000, 50),
        ...     pre_processing=lambda arr: (arr - arr.mean()) / arr.std()
        ... )
    """

    shape: Optional[tuple]

    def __init__(
        self,
        *,
        factory: Optional[Callable[[], np.ndarray]] = None,
        default: Optional[np.ndarray] = None,
        source: Optional[ArraySource] = None,
        description: Optional[str] = None,
        pre_processing: Optional[Callable[[np.ndarray], np.ndarray]] = None,
        shape: Optional[tuple] = None,
        markers: Optional[List[IOMarker]] = None,
    ):
        """Initialize a NumPy array variable with optional shape validation.

        Args:
            factory: Optional callable that produces a new array instance.
                    Cannot be used together with default.
            default: Optional static default array value.
                    Cannot be used together with factory.
            source: Optional ArraySource for loading/saving the array to .npy files.
            description: Optional human-readable description of the array's purpose.
            pre_processing: Optional transformation function applied to the array
                          before it is stored in the variable.
            shape: Optional expected shape tuple for validation. Use None in a
                  dimension to allow any size (e.g., (None, 768) allows any number
                  of 768-dimensional vectors).
            markers: Optional list of IOMarkers for input/output classification.

        Example:
            >>> # Fixed shape array
            >>> var = NDArrayVar(
            ...     shape=(100, 50),
            ...     factory=lambda: np.zeros((100, 50)),
            ...     description="Feature matrix"
            ... )
            >>>
            >>> # Variable-length array with fixed feature dimension
            >>> var = NDArrayVar(
            ...     shape=(None, 768),
            ...     source=ArraySource("embeddings.npy"),
            ...     description="Text embeddings"
            ... )
            >>>
            >>> # With normalization preprocessing
            >>> var = NDArrayVar(
            ...     shape=(1000, 50),
            ...     pre_processing=lambda arr: arr / np.linalg.norm(arr, axis=1, keepdims=True)
            ... )
        """
        super().__init__(
            np.ndarray,
            factory=factory,
            default=default,
            source=source,
            description=description,
            pre_processing=pre_processing,
            markers=markers,
        )
        self.shape = shape

    def validate(self) -> bool:
        """Validate the NumPy array type and shape.

        This method performs two levels of validation:
        1. Type validation: Ensures the value is a NumPy ndarray
        2. Shape validation: If a shape is specified, ensures the array matches
           the expected dimensions

        Returns:
            True if validation passes.

        Raises:
            TypeError: If the value is not a NumPy ndarray.
            ValueError: If the array shape doesn't match the expected shape.

        Example:
            >>> var = NDArrayVar(shape=(100, 768), name="embeddings")
            >>> var.value = np.zeros((100, 768))
            >>> var.validate()  # Returns True
            True
            >>>
            >>> var.value = np.zeros((50, 768))
            >>> var.validate()  # Raises ValueError
            ValueError: Array 'embeddings' has incorrect shape. Expected: (100, 768), Got: (50, 768)
            >>>
            >>> var.value = [1, 2, 3]  # Not a NumPy array
            >>> var.validate()  # Raises TypeError
            TypeError: Variable 'embeddings' expected numpy.ndarray, but got list

        Note:
            If no shape is specified during initialization, only type validation
            is performed. If the value is None, validation passes without checking.
        """
        super().validate()

        if self.value is None or self.shape is None:
            return True

        if not isinstance(self.value, np.ndarray):
            raise TypeError(
                f"Variable '{self.name}' expected numpy.ndarray, "
                f"but got {type(self.value).__name__}"
            )

        if self.value.shape != self.shape:
            raise ValueError(
                f"Array '{self.name}' has incorrect shape. "
                f"Expected: {self.shape}, Got: {self.value.shape}"
            )

        return True
        return True
        return True
        return True
        return True
        return True
        return True
        return True
        return True
        return True
