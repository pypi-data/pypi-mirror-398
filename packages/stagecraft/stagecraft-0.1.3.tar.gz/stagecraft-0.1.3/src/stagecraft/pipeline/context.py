"""Pipeline context for variable passing between stages.

This module provides the PipelineContext class, which serves as a runtime container
for managing variables that are passed between different stages of a data pipeline.
It includes memory tracking capabilities and automatic cleanup of unused variables
to optimize memory usage during pipeline execution.
"""

from typing import Any, Dict, Optional, Set

from .memory import MemoryConfig, MemoryManager

_MISSING = object()


class PipelineContext:
    """Runtime context for variable passing between pipeline stages.

    PipelineContext manages the lifecycle of variables that flow through a multi-stage
    data pipeline. It provides a centralized storage mechanism with optional memory
    tracking and automatic cleanup capabilities to prevent memory bloat in long-running
    pipelines.

    The context supports:
    - Setting and retrieving variables with type safety
    - Memory usage tracking per variable
    - Automatic clearing of variables no longer needed by downstream stages
    - Manual variable cleanup for fine-grained memory management

    Attributes:
        memory_manager: Manages memory tracking and cleanup operations.
        _variables: Read-only access to the internal variables dictionary.
    """

    def __init__(
        self,
        initial_vars: Optional[Dict[str, Any]] = None,
        memory_config: Optional[MemoryConfig] = None,
    ):
        """Initialize the pipeline context.

        Args:
            initial_vars: Optional dictionary of initial variables to populate the context.
                         Useful for providing input data or configuration at pipeline start.
            memory_config: Optional configuration for memory tracking and management.
                          If provided with enabled=True, memory usage will be tracked.
        """
        self._variables: Dict[str, Any] = initial_vars or {}
        self.memory_manager = MemoryManager(memory_config)

        if memory_config and memory_config.enabled:
            for name, value in self._variables.items():
                self.memory_manager.tracker.track_variable(name, value)

    def set(self, name: str, value: Any):
        """Store a variable in the pipeline context.

        This method adds or updates a variable in the context. If memory tracking
        is enabled with per-variable tracking, the memory usage of the variable
        will be recorded.

        Args:
            name: The name of the variable to store. Must be a non-empty string.
            value: The value to store. Can be any Python object.

        Raises:
            ValueError: If the variable name is empty.

        Example:
            >>> context = PipelineContext()
            >>> context.set("data", pd.DataFrame())
            >>> context.set("model", trained_model)
        """
        if not name:
            raise ValueError("Variable name cannot be empty")

        self._variables[name] = value

        if self.memory_manager.config.enabled and self.memory_manager.config.track_per_variable:
            self.memory_manager.tracker.track_variable(name, value)

    def get(self, name: str, default: Optional[Any] = _MISSING) -> Any:
        """Retrieve a variable from the pipeline context.

        This method fetches a variable by name. If the variable doesn't exist,
        it either returns a default value (if provided) or raises a descriptive
        KeyError with available variable names to aid debugging.

        Args:
            name: The name of the variable to retrieve.
            default: Optional default value to return if the variable is not found.
                    If not provided, a KeyError will be raised for missing variables.

        Returns:
            The value of the requested variable, or the default value if provided
            and the variable doesn't exist.

        Raises:
            KeyError: If the variable is not found and no default value is provided.
                     The error message includes a list of available variables.

        Example:
            >>> context = PipelineContext()
            >>> context.set("data", [1, 2, 3])
            >>> context.get("data")
            [1, 2, 3]
            >>> context.get("missing", default=None)
            None
            >>> context.get("missing")  # Raises KeyError
        """
        if not self.has(name):
            if default is not _MISSING:
                return default
            available_vars = list(self._variables.keys())
            raise KeyError(
                f"Variable '{name}' not found in pipeline context. "
                f"Check that the variable is produced by a previous stage. "
                f"Available variables: {available_vars}."
            )
        return self._variables[name]

    def has(self, name: str) -> bool:
        """Check if a variable exists in the pipeline context.

        Args:
            name: The name of the variable to check.

        Returns:
            True if the variable exists in the context, False otherwise.

        Example:
            >>> context = PipelineContext()
            >>> context.set("data", [1, 2, 3])
            >>> context.has("data")
            True
            >>> context.has("missing")
            False
        """
        return name in self._variables

    def clear_variable(self, name: str) -> bool:
        """
        Clear a variable from context to free memory.

        Args:
            name: Name of the variable to clear

        Returns:
            True if variable was cleared, False otherwise
        """
        if not self.has(name):
            return False
        return self.memory_manager.clear_variable(name, self._variables)

    def clear_variables(self, names: Set[str]) -> int:
        """
        Clear multiple variables from context.

        Args:
            names: Set of variable names to clear

        Returns:
            Number of variables successfully cleared
        """
        cleared_count = 0
        for name in names:
            if self.clear_variable(name):
                cleared_count += 1
        return cleared_count

    def auto_clear_unused_variables(
        self, required_by_map: Dict[str, Set[str]], completed_stages: Set[str]
    ) -> int:
        """
        Automatically clear variables that are no longer needed.

        Args:
            required_by_map: Map of variable name to set of stage names that require it
            completed_stages: Set of stage names that have completed execution

        Returns:
            Number of variables cleared
        """
        if not self.memory_manager.config.auto_clear_enabled:
            return 0

        cleared_count = 0
        variables_to_clear = []

        for var_name in self._variables.keys():
            required_by = required_by_map.get(var_name, set())
            if self.memory_manager.can_clear_variable(var_name, required_by, completed_stages):
                variables_to_clear.append(var_name)

        for var_name in variables_to_clear:
            if self.clear_variable(var_name):
                cleared_count += 1

        return cleared_count

    def get_memory_summary(self) -> Dict[str, Any]:
        """Get a summary of current memory usage.

        Returns:
            A dictionary containing memory usage statistics, including total memory
            used by tracked variables and per-variable breakdowns if available.

        Example:
            >>> context = PipelineContext(memory_config=MemoryConfig(enabled=True))
            >>> context.set("data", large_dataframe)
            >>> summary = context.get_memory_summary()
            >>> print(summary["total_memory_mb"])
        """
        return self.memory_manager.get_summary()

    def log_memory_summary(self) -> None:
        """Log the current memory usage summary.

        This method outputs memory usage information to the logger, useful for
        monitoring and debugging memory consumption during pipeline execution.

        Example:
            >>> context = PipelineContext(memory_config=MemoryConfig(enabled=True))
            >>> context.set("data", large_dataframe)
            >>> context.log_memory_summary()  # Logs memory stats
        """
        self.memory_manager.tracker.log_summary()

    @property
    def variables(self) -> Dict[str, Any]:
        """Provide read-only access to the internal variables dictionary.

        This property is provided for compatibility and introspection purposes.
        Direct modification of the returned dictionary is discouraged; use the
        set() and clear_variable() methods instead.

        Returns:
            The internal dictionary mapping variable names to their values.

        Example:
            >>> context = PipelineContext()
            >>> context.set("x", 10)
            >>> context.set("y", 20)
            >>> list(context.variables.keys())
            ['x', 'y']
        """
        return self._variables

    def __str__(self):
        """Return a string representation of the pipeline context.

        Returns:
            A string showing the class name and list of variable names currently
            stored in the context.

        Example:
            >>> context = PipelineContext()
            >>> context.set("data", [1, 2, 3])
            >>> context.set("model", "classifier")
            >>> str(context)
            "PipelineContext(['data', 'model'])"
        """
        return f"PipelineContext({list(self._variables.keys())})"
