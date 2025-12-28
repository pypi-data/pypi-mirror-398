"""Descriptor functions for declaring stage variable inputs and outputs.

This module provides three descriptor functions that are used as class-level
decorators in ETL stage definitions to declare how variables flow through stages:

- sconsume: Marks a variable as an input (consumed by the stage)
- sproduce: Marks a variable as an output (produced by the stage)
- stransform: Marks a variable as both input and output (transformed by the stage)

These descriptors enable declarative specification of data dependencies and outputs,
which the pipeline framework uses for:
- Dependency validation
- Data flow tracking
- Automatic variable loading and saving
- Pipeline optimization

Example:
    >>> class MyStage(ETLStage):
    ...     name = "my_stage"
    ...     input_data = sconsume(pd.DataFrame)
    ...     output_data = sproduce(pd.DataFrame)
    ...     config = stransform(dict)
"""

from typing import Optional, Type, Union

from .markers import IOMarker
from .variables import _T, SVar


def sconsume(var: Optional[Union[SVar[_T], Type[_T]]] = None, /) -> SVar:
    """Declare a stage variable as an input (consumed).

    This descriptor marks a variable as an input to the stage, meaning the stage
    will read this variable from the pipeline context but will not modify it.
    The variable must be available either from:
    - A previous stage's output
    - The initial pipeline context
    - A configured data source with load capability

    Args:
        var: Optional specification of the variable:
            - None: Type will be inferred from the class attribute annotation
            - Type[_T]: A type hint (e.g., pd.DataFrame, dict, str)
            - SVar[_T]: An existing SVar instance to be marked as input

    Returns:
        An SVar instance marked with IOMarker.INPUT, indicating this variable
        is consumed by the stage.

    Example:
        >>> class LoadStage(ETLStage):
        ...     # Infer type from annotation
        ...     file_path: str = sconsume()
        ...
        >>> class ProcessStage(ETLStage):
        ...     # Explicit type
        ...     raw_data = sconsume(pd.DataFrame)
        ...
        >>> class AnalyzeStage(ETLStage):
        ...     # With data source
        ...     data = sconsume(DFVar(
        ...         DataSchema,
        ...         source=CSVSource("data.csv"),
        ...     ))

    Note:
        Variables marked with sconsume() are read-only from the stage's perspective.
        To modify a variable, use stransform() instead.
    """
    if var is None:
        variable = SVar(markers=[IOMarker.INPUT])
    elif isinstance(var, SVar):
        variable = var
        variable.set_markers([IOMarker.INPUT])
    else:
        variable = SVar(var, markers=[IOMarker.INPUT])
    return variable


def sproduce(var: Optional[Union[SVar[_T], Type[_T]]] = None, /) -> SVar:
    """Declare a stage variable as an output (produced).

    This descriptor marks a variable as an output of the stage, meaning the stage
    will create or compute this variable and make it available to subsequent stages
    in the pipeline. The variable will be stored in the pipeline context after the
    stage executes.

    Output variables can optionally be configured with a data source for automatic
    persistence to disk.

    Args:
        var: Optional specification of the variable:
            - None: Type will be inferred from the class attribute annotation
            - Type[_T]: A type hint (e.g., pd.DataFrame, dict, str)
            - SVar[_T]: An existing SVar instance to be marked as output

    Returns:
        An SVar instance marked with IOMarker.OUTPUT, indicating this variable
        is produced by the stage.

    Example:
        >>> class ExtractStage(ETLStage):
        ...     # Infer type from annotation
        ...     raw_data: pd.DataFrame = sproduce()
        ...
        >>> class TransformStage(ETLStage):
        ...     # Explicit type
        ...     processed_data = sproduce(pd.DataFrame)
        ...
        >>> class SaveStage(ETLStage):
        ...     # With data source for automatic saving
        ...     results = sconsume(DFVar(
        ...         ResultSchema,
        ...         source=CSVSource("output/results.csv"),
        ...     ))

    Note:
        The stage's execute() method is responsible for setting the value of
        output variables in the context. Variables marked with sproduce() should
        not be read from the context before being set.
    """
    if var is None:
        variable = SVar(markers=[IOMarker.OUTPUT])
    elif isinstance(var, SVar):
        variable = var
        variable.set_markers([IOMarker.OUTPUT])
    else:
        variable = SVar(var, markers=[IOMarker.OUTPUT])
    return variable


def stransform(var: Optional[Union[SVar[_T], Type[_T]]] = None, /) -> SVar:
    """Declare a stage variable as both input and output (transformed).

    This descriptor marks a variable as both an input and output of the stage,
    meaning the stage will:
    1. Read the variable from the pipeline context (or data source)
    2. Modify or transform it
    3. Write the updated value back to the context

    This is useful for incremental transformations where a variable is progressively
    modified through multiple stages, or for in-place updates to shared state.

    Args:
        var: Optional specification of the variable:
            - None: Type will be inferred from the class attribute annotation
            - Type[_T]: A type hint (e.g., pd.DataFrame, dict, str)
            - SVar[_T]: An existing SVar instance to be marked as input/output

    Returns:
        An SVar instance marked with both IOMarker.INPUT and IOMarker.OUTPUT,
        indicating this variable is both consumed and produced by the stage.

    Example:
        >>> class EnrichStage(ETLStage):
        ...     # Read, modify, and write back
        ...     data: pd.DataFrame = stransform()
        ...
        >>> class AccumulateStage(ETLStage):
        ...     # Explicit type
        ...     metrics = stransform(dict)
        ...
        >>> class UpdateConfigStage(ETLStage):
        ...     # With data source for load and save
        ...     config = stransform(SVar(
        ...         dict,
        ...         source=JSONSource("config.json", mode="w+")
        ...     ))

    Note:
        The stage's execute() method should read the current value from the context,
        modify it, and then set the updated value back. The variable must be available
        from a previous stage, initial context, or loadable data source.

    Warning:
        Be cautious with stransform() when using parallel execution, as it creates
        a read-modify-write pattern that may lead to race conditions if multiple
        stages transform the same variable concurrently.
    """
    if var is None:
        variable = SVar(markers=[IOMarker.INPUT, IOMarker.OUTPUT])
    elif isinstance(var, SVar):
        variable = var
        variable.set_markers([IOMarker.INPUT, IOMarker.OUTPUT])
    else:
        variable = SVar(var, markers=[IOMarker.INPUT, IOMarker.OUTPUT])
    return variable
