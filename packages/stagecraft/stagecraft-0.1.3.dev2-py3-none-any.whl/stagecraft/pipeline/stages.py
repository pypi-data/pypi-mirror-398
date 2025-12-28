"""Base classes and infrastructure for ETL pipeline stages.

This module provides the ETLStage abstract base class, which serves as the foundation
for all pipeline stages. ETLStage handles:

- Variable management (inputs, outputs, transformations)
- Context injection and data flow
- Conditional execution
- Input loading and output saving
- Dynamic property access for stage variables
- Metadata generation

Stages are the fundamental building blocks of pipelines. Each stage:
1. Declares its input and output variables using descriptors (sconsume, sproduce, stransform)
2. Implements a recipe() method containing the transformation logic
3. Can be conditionally executed based on runtime state
4. Automatically loads inputs and saves outputs

Example:
    >>> class MyStage(ETLStage):
    ...     name = "my_stage"
    ...     input_data = sconsume(pd.DataFrame)
    ...     output_data = sproduce(pd.DataFrame)
    ...
    ...     def recipe(self):
    ...         self.output_data = self.input_data.copy()
    ...         self.output_data['new_col'] = 1
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..core.wrappers import handle_exceptions
from .conditions import AlwaysExecute, StageCondition
from .context import PipelineContext
from .markers import IOMarker
from .pipeline_metadata import StageMetadata, StageParameter
from .variables import SVar


class ETLStage(ABC):
    """Abstract base class for all ETL pipeline stages.

    ETLStage provides the infrastructure for building modular, composable data
    transformation stages. It manages the lifecycle of stage variables, handles
    data flow between stages through the pipeline context, and provides hooks
    for conditional execution.

    Subclasses must:
    - Define a unique 'name' attribute (or pass it to __init__)
    - Implement the recipe() method with transformation logic
    - Declare variables using sconsume(), sproduce(), or stransform() descriptors

    The stage execution flow is:
    1. Check condition (should_execute())
    2. Load inputs from context or data sources (load_inputs())
    3. Execute transformation logic (recipe())
    4. Save outputs to context or data sources (save_outputs())
    5. Clear variables from memory (__clear_variables())

    Attributes:
        name: Unique identifier for the stage within a pipeline.
        description: Optional human-readable description of the stage's purpose.
        context: The pipeline context for variable storage and retrieval.
        parameters: List of configurable parameters for the stage.
        condition: Condition determining whether the stage should execute.
        _vars: Internal mapping of variable names to SVar instances.
        _input_keys: List of variable names marked as inputs.
        _output_keys: List of variable names marked as outputs.
        _dynamic_props: Internal mapping for dynamic property access.

    Example:
        >>> class TransformStage(ETLStage):
        ...     name = "transform"
        ...     description = "Apply transformations to raw data"
        ...     raw_data = sconsume(pd.DataFrame)
        ...     clean_data = sproduce(pd.DataFrame)
        ...
        ...     def recipe(self):
        ...         df = self.raw_data.copy()
        ...         df = df.dropna()
        ...         df['processed'] = True
        ...         self.clean_data = df
    """

    def __init__(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        context: Optional[PipelineContext] = None,
        parameters: Optional[List[StageParameter]] = None,
        condition: Optional[StageCondition] = None,
    ):
        """Initialize an ETL stage.

        Args:
            name: Optional stage name. If not provided, uses the class name.
            description: Optional description of the stage's purpose.
            context: Optional pipeline context. Usually set by the pipeline runner.
            parameters: Optional list of stage parameters for configuration.
            condition: Optional execution condition. Defaults to AlwaysExecute.

        Example:
            >>> stage = MyStage(
            ...     name="custom_name",
            ...     description="Processes customer data",
            ...     parameters=[StageParameter("threshold", 0.5)]
            ... )
        """
        self.name = name or self.__class__.__name__
        self.description = description
        self.context = context
        self.parameters = parameters or []
        self.condition: StageCondition = condition or getattr(
            self.__class__, "condition", AlwaysExecute()
        )
        self._vars: Dict[str, SVar] = {}
        self._input_keys: List[str] = []
        self._output_keys: List[str] = []
        self._dynamic_props: Dict[str, Dict[str, Any]] = {}
        self.__inject_pending_variables()

    def __inject_pending_variables(self):
        """Inject variables that were declared as class attributes.

        This internal method processes variables declared using descriptors
        (sconsume, sproduce, stransform) at the class level. It's called
        during __init__ to register these variables with the stage.

        Note:
            This is an internal method and should not be called directly.
        """
        if not hasattr(self, "_pending_variables"):
            return

        while self._pending_variables:  # type: ignore
            var, markers = self._pending_variables.pop(0)  # type: ignore
            self.add_variable(var, markers)

    def set_context(self, context: PipelineContext):
        """Inject or replace the pipeline context for this stage.

        This method sets the pipeline context for the stage and propagates it
        to all registered variables. The context is used for storing and
        retrieving variable values during pipeline execution.

        Args:
            context: The pipeline context to inject. Cannot be None.

        Raises:
            ValueError: If context is None.

        Example:
            >>> stage = MyStage()
            >>> context = PipelineContext()
            >>> stage.set_context(context)
            >>> assert stage.context is context
        """
        if context is None:
            raise ValueError(f"Cannot set None as context for stage '{self.name}'")

        self.context = context
        for var in self._vars.values():
            var.set_context(context)

    def add_consumed(self, *var: SVar):
        """Add one or more variables as inputs (consumed) to this stage.

        Args:
            *var: One or more SVar instances to mark as inputs.

        Example:
            >>> stage = MyStage()
            >>> data_var = SVar(pd.DataFrame, name="data")
            >>> stage.add_consumed(data_var)
        """
        for v in var:
            self.add_variable(v, [IOMarker.INPUT])

    def add_produced(self, *var: SVar):
        """Add one or more variables as outputs (produced) by this stage.

        Args:
            *var: One or more SVar instances to mark as outputs.

        Example:
            >>> stage = MyStage()
            >>> result_var = SVar(pd.DataFrame, name="result")
            >>> stage.add_produced(result_var)
        """
        for v in var:
            self.add_variable(v, [IOMarker.OUTPUT])

    def add_transformed(self, *var: SVar):
        """Add one or more variables as both inputs and outputs (transformed).

        Args:
            *var: One or more SVar instances to mark as input/output.

        Example:
            >>> stage = MyStage()
            >>> data_var = SVar(pd.DataFrame, name="data")
            >>> stage.add_transformed(data_var)
        """
        for v in var:
            self.add_variable(v, [IOMarker.INPUT, IOMarker.OUTPUT])

    def add_variable(self, var: SVar, markers: List[IOMarker]):
        """Register a variable with the stage and configure its I/O markers.

        This method registers a variable with the stage, marking it as an input,
        output, or both. It also sets up dynamic property access so the variable
        can be accessed as a stage attribute.

        Args:
            var: The SVar instance to register.
            markers: List of IOMarker values indicating whether the variable is
                    an INPUT, OUTPUT, or both.

        Raises:
            ValueError: If an invalid marker is provided or if the variable has
                       no name.

        Example:
            >>> stage = MyStage()
            >>> var = SVar(pd.DataFrame, name="data")
            >>> stage.add_variable(var, [IOMarker.INPUT])
            >>> # Now can access as: stage.data

        Note:
            This method is typically called automatically by the descriptor
            functions (sconsume, sproduce, stransform) and should rarely be
            called directly.
        """
        for marker in markers:
            if marker == IOMarker.INPUT:
                self._input_keys.append(var.name)
            elif marker == IOMarker.OUTPUT:
                self._output_keys.append(var.name)
            else:
                raise ValueError(f"Invalid variable marker: {marker}")

        name = var.name
        if not name:
            raise ValueError(
                "Variable name is not set. Ensure the variable is properly initialized in a class."
            )

        def deleter(name: str):
            del self._vars[name]

        self._vars[name] = var
        self._dynamic_props[name] = {
            "getter": self._vars[name].get,
            "setter": self._vars[name].set,
            "deleter": lambda: deleter(name),
        }

    def load_inputs(self):
        """Load all input variables from the pipeline context or data sources.

        This method iterates through all variables marked as inputs and loads
        their values. Variables can be loaded from:
        1. The pipeline context (set by previous stages)
        2. Configured data sources (e.g., CSVSource, JSONSource)

        Raises:
            ValueError: If any input fails to load. The error message includes
                       the variable name and original error for debugging.

        Example:
            >>> stage = MyStage()
            >>> stage.set_context(context)
            >>> stage.load_inputs()  # Loads all input variables

        Note:
            This method is called automatically by execute() before recipe().
            It should rarely need to be called manually.
        """
        try:
            for name in self._input_keys:
                self._vars[name].load()
        except Exception as e:
            raise ValueError(
                f"Failed to load input '{name}' for stage '{self.name}'. "
                f"Ensure the variable exists in context and has the correct type.\n"
                f"Original error: {str(e)}"
            ) from e

    def save_outputs(self):
        """Save all output variables to the pipeline context or data sources.

        This method iterates through all variables marked as outputs and saves
        their values. Variables can be saved to:
        1. The pipeline context (for use by subsequent stages)
        2. Configured data sources (e.g., CSVSource, JSONSource)

        Raises:
            ValueError: If any output fails to save. The error message includes
                       the variable name and original error for debugging.

        Example:
            >>> stage = MyStage()
            >>> stage.set_context(context)
            >>> stage.output_data = processed_df
            >>> stage.save_outputs()  # Saves all output variables

        Note:
            This method is called automatically by execute() after recipe().
            It should rarely need to be called manually.
        """
        try:
            for name in self._output_keys:
                self._vars[name].save()
        except Exception as e:
            raise ValueError(
                f"Failed to save output '{name}' for stage '{self.name}'. "
                f"Ensure the output value is set and valid.\n"
                f"Original error: {str(e)}"
            ) from e

    def __clear_variables(self):
        """Clear all variables from memory after stage execution.

        This internal method removes all variable references to allow garbage
        collection. It's called automatically at the end of execute() to
        prevent memory leaks in long-running pipelines.

        Note:
            This is an internal method and should not be called directly.
        """
        while self._vars:
            del self._vars[next(iter(self._vars))]
        self._input_keys.clear()
        self._output_keys.clear()
        self._dynamic_props.clear()

    def should_execute(self) -> bool:
        """Check if this stage should execute based on its condition.

        This method evaluates the stage's execution condition to determine
        whether the stage should run. Conditions can be based on:
        - Context variables
        - Previous stage results
        - External state
        - Custom logic

        Returns:
            True if the stage should execute, False to skip execution.

        Example:
            >>> class ConditionalStage(ETLStage):
            ...     name = "conditional"
            ...     condition = VariableExistsCondition("trigger")
            ...
            >>> stage = ConditionalStage()
            >>> stage.set_context(context)
            >>> if stage.should_execute():
            ...     stage.execute()

        Note:
            If no context is set, this method returns True (always execute).
        """
        if self.context is None:
            return True

        return self.condition.should_execute(self.context, self.name)

    def get_skip_reason(self) -> str:
        """Get the reason why this stage was skipped.

        This method returns a human-readable explanation of why the stage's
        condition evaluated to False, useful for logging and debugging.

        Returns:
            A string describing why the stage was skipped.

        Example:
            >>> stage = ConditionalStage()
            >>> if not stage.should_execute():
            ...     reason = stage.get_skip_reason()
            ...     logger.info(f"Skipping {stage.name}: {reason}")
        """
        return self.condition.get_skip_reason()

    def execute(self):
        """Execute the complete stage lifecycle.

        This method orchestrates the full execution of the stage:
        1. Ensures a context is available (creates one if needed)
        2. Loads all input variables
        3. Executes the recipe() method with configured parameters
        4. Saves all output variables
        5. Clears variables from memory

        Raises:
            RuntimeError: If stage execution fails at any step. The original
                         error is included in the exception chain.

        Example:
            >>> stage = MyStage()
            >>> stage.set_context(context)
            >>> stage.execute()  # Runs the complete stage lifecycle

        Note:
            This method is typically called by the pipeline runner rather than
            directly. For standalone execution, ensure the context is set first.
        """
        if self.context is None:
            self.set_context(PipelineContext())

        try:
            self.load_inputs()
            parameter_dict = {param.name: param.value for param in self.parameters}
            self.__safe_recipe(**parameter_dict)
            self.save_outputs()
        except Exception as e:
            raise RuntimeError(
                f"Stage '{self.name}' execution failed. "
                f"Check the stage's recipe() method and input/output variables.\n"
                f"Original error: {str(e)}"
            ) from e
        self.__clear_variables()

    @abstractmethod
    def recipe(self, **kwargs):
        """Define the transformation logic for this stage.

        This abstract method must be implemented by all stage subclasses. It
        contains the core business logic that transforms inputs into outputs.

        The recipe method should:
        1. Read input variables as stage attributes (e.g., self.input_data)
        2. Perform transformations
        3. Set output variables as stage attributes (e.g., self.output_data = result)

        Args:
            **kwargs: Stage parameters passed from the parameters list. Parameter
                     names become keyword argument names.

        Example:
            >>> class MyStage(ETLStage):
            ...     name = "my_stage"
            ...     input_data = sconsume(pd.DataFrame)
            ...     output_data = sproduce(pd.DataFrame)
            ...
            ...     def recipe(self, threshold=0.5):
            ...         df = self.input_data.copy()
            ...         df = df[df['score'] > threshold]
            ...         self.output_data = df

        Note:
            Do not call load_inputs() or save_outputs() in recipe(). These are
            handled automatically by execute().
        """
        pass

    @handle_exceptions
    def __safe_recipe(self, **kwargs):
        """Execute the recipe in a controlled environment.

        This internal method wraps the recipe() call with exception handling
        and logging. It's called by execute() to run the user-defined recipe.

        Args:
            **kwargs: Parameters to pass to recipe().

        Note:
            This is an internal method and should not be called directly.
        """
        self.recipe(**kwargs)

    def get_metadata(self) -> StageMetadata:
        """Get metadata describing this stage's configuration.

        This method generates a StageMetadata object containing information
        about the stage's name and parameters. Metadata is used for:
        - Pipeline documentation
        - Execution tracking
        - Debugging and monitoring

        Returns:
            A StageMetadata object containing the stage's name and parameters.

        Example:
            >>> stage = MyStage(
            ...     name="process",
            ...     parameters=[StageParameter("threshold", 0.5)]
            ... )
            >>> metadata = stage.get_metadata()
            >>> print(metadata.name)
            process
            >>> print(metadata.parameters[0].name)
            threshold
        """
        return StageMetadata(name=self.name, parameters=self.parameters)

    def __getattr__(self, item):
        """Enable dynamic property access for stage variables.

        This magic method allows accessing stage variables as attributes.
        When you access a variable (e.g., self.input_data), it triggers the
        variable's getter to retrieve the value from the context.

        Args:
            item: The attribute name being accessed.

        Returns:
            The value of the variable from the context.

        Raises:
            AttributeError: If the attribute is not a registered variable.

        Example:
            >>> class MyStage(ETLStage):
            ...     input_data = sconsume(pd.DataFrame)
            ...
            >>> stage = MyStage()
            >>> # Accessing input_data triggers __getattr__
            >>> df = stage.input_data  # Calls SVar.get()
        """
        if item in self._dynamic_props:
            return self._dynamic_props[item]["getter"]()
        raise AttributeError(f"{type(self).__name__!r} object has no attribute {item!r}")

    def __setattr__(self, key, value):
        """Enable dynamic property setting for stage variables.

        This magic method allows setting stage variables as attributes.
        When you set a variable (e.g., self.output_data = df), it triggers
        the variable's setter to store the value in the context.

        Args:
            key: The attribute name being set.
            value: The value to set.

        Example:
            >>> class MyStage(ETLStage):
            ...     output_data = sproduce(pd.DataFrame)
            ...
            >>> stage = MyStage()
            >>> # Setting output_data triggers __setattr__
            >>> stage.output_data = df  # Calls SVar.set()
        """
        if "_dynamic_props" in self.__dict__ and key in self.__dict__.get("_dynamic_props", {}):
            return self._dynamic_props[key]["setter"](value)
        super().__setattr__(key, value)

    def __delattr__(self, item):
        """Enable dynamic property deletion for stage variables.

        This magic method allows deleting stage variables as attributes.
        It removes the variable from the stage's internal tracking.

        Args:
            item: The attribute name being deleted.

        Example:
            >>> stage = MyStage()
            >>> del stage.input_data  # Removes variable from stage
        """
        if item in self._dynamic_props:
            self._dynamic_props[item]["deleter"]()
            del self._dynamic_props[item]
        super().__delattr__(item)

    def __str__(self):
        """Return a string representation of the stage.

        Returns:
            A string showing the stage class and name.

        Example:
            >>> stage = MyStage(name="process")
            >>> str(stage)
            'ETLStage(process)'
        """
        return f"ETLStage({self.name})"

    def __repr__(self):
        """Return a detailed string representation of the stage.

        Returns:
            Same as __str__() for this class.
        """
        return self.__str__()
