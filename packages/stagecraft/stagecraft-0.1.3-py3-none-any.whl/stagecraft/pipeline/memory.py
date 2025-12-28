"""Memory tracking and management for pipeline execution.

This module provides utilities for monitoring and controlling memory usage during
pipeline execution. It includes:

- Memory tracking for individual variables
- Automatic cleanup of variables no longer needed
- Memory usage warnings and logging
- Support for common data types (DataFrames, arrays, dicts, lists)

The memory management system helps prevent out-of-memory errors in long-running
pipelines by automatically clearing variables that are no longer needed by
downstream stages.

Example:
    >>> config = MemoryConfig(
    ...     enabled=True,
    ...     warning_threshold_mb=500.0,
    ...     auto_clear_enabled=True
    ... )
    >>> manager = MemoryManager(config)
    >>> context_vars = {"data": large_dataframe}
    >>> manager.tracker.track_variable("data", large_dataframe)
"""

import gc
import logging
import sys
from dataclasses import dataclass
from typing import Any, Dict, Optional, Set

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class MemoryConfig:
    """Configuration for memory tracking and management.

    This dataclass defines the behavior of the memory management system,
    controlling when and how memory tracking and cleanup occur.

    Attributes:
        enabled: Whether memory tracking is enabled. If False, no tracking occurs.
        warning_threshold_mb: Memory size in MB above which a warning is logged
                             when a variable is tracked. Default is 1000 MB (1 GB).
        auto_clear_enabled: Whether automatic variable cleanup is enabled. If True,
                           variables are automatically cleared when no longer needed.
        track_per_variable: Whether to track memory usage for each individual variable.
                           If False, only aggregate tracking occurs.
        log_memory_usage: Whether to log memory usage information. If True, logs are
                         emitted when variables are tracked, cleared, or summarized.

    Example:
        >>> # Conservative configuration for memory-constrained environments
        >>> config = MemoryConfig(
        ...     enabled=True,
        ...     warning_threshold_mb=500.0,
        ...     auto_clear_enabled=True,
        ...     track_per_variable=True,
        ...     log_memory_usage=True
        ... )
        >>>
        >>> # Minimal tracking for performance
        >>> minimal_config = MemoryConfig(
        ...     enabled=True,
        ...     track_per_variable=False,
        ...     log_memory_usage=False
        ... )
    """

    enabled: bool = True
    warning_threshold_mb: float = 1000.0
    auto_clear_enabled: bool = True
    track_per_variable: bool = True
    log_memory_usage: bool = True


@dataclass
class VariableMemoryInfo:
    """Information about a variable's memory usage.

    This dataclass encapsulates metadata about a tracked variable's memory
    footprint, including its name, size, and type.

    Attributes:
        name: The name of the variable in the pipeline context.
        size_bytes: The memory size of the variable in bytes.
        type_name: The Python type name of the variable (e.g., "DataFrame", "ndarray").

    Example:
        >>> info = VariableMemoryInfo(
        ...     name="large_data",
        ...     size_bytes=104857600,
        ...     type_name="DataFrame"
        ... )
        >>> print(f"{info.name}: {info.size_mb:.2f} MB")
        large_data: 100.00 MB
    """

    name: str
    size_bytes: int
    type_name: str

    @property
    def size_mb(self) -> float:
        """Convert size from bytes to megabytes.

        Returns:
            The memory size in megabytes (MB).

        Example:
            >>> info = VariableMemoryInfo("data", 1048576, "DataFrame")
            >>> info.size_mb
            1.0
        """
        return self.size_bytes / (1024 * 1024)


class MemoryTracker:
    """Tracks memory usage of pipeline variables.

    MemoryTracker monitors the memory footprint of variables in the pipeline
    context, providing accurate size calculations for common data types and
    maintaining statistics about memory usage over time.

    The tracker supports:
    - Accurate memory calculation for DataFrames (including deep memory usage)
    - NumPy array memory tracking
    - Recursive size calculation for collections (lists, dicts, tuples)
    - Fallback to sys.getsizeof for other types
    - Cumulative tracking of cleared memory

    Attributes:
        config: The memory configuration controlling tracking behavior.
        _variable_sizes: Internal mapping of variable names to their sizes in bytes.
        _total_cleared_bytes: Cumulative total of memory cleared during execution.

    Example:
        >>> tracker = MemoryTracker(MemoryConfig(enabled=True))
        >>> df = pd.DataFrame({"col": range(1000)})
        >>> info = tracker.track_variable("my_data", df)
        >>> print(f"Tracked {info.size_mb:.2f} MB")
    """

    def __init__(self, config: Optional[MemoryConfig] = None):
        """Initialize the memory tracker.

        Args:
            config: Optional memory configuration. If None, uses default MemoryConfig.

        Example:
            >>> config = MemoryConfig(warning_threshold_mb=500.0)
            >>> tracker = MemoryTracker(config)
        """
        self.config = config or MemoryConfig()
        self._variable_sizes: Dict[str, int] = {}
        self._total_cleared_bytes: int = 0

    def get_object_size(self, obj: Any) -> int:
        """Calculate the memory size of an object in bytes.

        This method provides accurate memory size calculation for common data types
        used in pipelines. It handles:
        - pandas DataFrames: Uses deep memory usage including object dtypes
        - NumPy arrays: Uses nbytes for accurate array memory
        - Collections (list, tuple, dict): Recursively calculates total size
        - Other objects: Falls back to sys.getsizeof

        Args:
            obj: The object to measure. Can be any Python object.

        Returns:
            The memory size in bytes.

        Example:
            >>> tracker = MemoryTracker()
            >>> df = pd.DataFrame({"a": [1, 2, 3]})
            >>> size = tracker.get_object_size(df)
            >>> print(f"DataFrame size: {size} bytes")
            >>>
            >>> arr = np.zeros((1000, 1000))
            >>> size = tracker.get_object_size(arr)
            >>> print(f"Array size: {size / 1024 / 1024:.2f} MB")

        Note:
            For nested collections, this method recursively calculates the total
            size, which may be slower for deeply nested structures.
        """
        if isinstance(obj, pd.DataFrame):
            return int(obj.memory_usage(deep=True).sum())
        elif isinstance(obj, np.ndarray):
            return int(obj.nbytes)
        elif isinstance(obj, (list, tuple)):
            return sum(self.get_object_size(item) for item in obj)
        elif isinstance(obj, dict):
            return sum(self.get_object_size(k) + self.get_object_size(v) for k, v in obj.items())
        else:
            return sys.getsizeof(obj)

    def track_variable(self, name: str, value: Any) -> VariableMemoryInfo:
        """Track the memory usage of a variable.

        This method calculates and records the memory size of a variable,
        optionally logging the information and emitting warnings if the size
        exceeds the configured threshold.

        Args:
            name: The name of the variable to track. Must be non-empty.
            value: The value to track. Cannot be None.

        Returns:
            A VariableMemoryInfo object containing the variable's metadata.

        Raises:
            ValueError: If name is empty or value is None.
            RuntimeError: If memory size calculation fails. The original error
                         is included in the exception chain.

        Example:
            >>> tracker = MemoryTracker(MemoryConfig(
            ...     log_memory_usage=True,
            ...     warning_threshold_mb=100.0
            ... ))
            >>> df = pd.DataFrame({"col": range(10000)})
            >>> info = tracker.track_variable("data", df)
            >>> print(f"{info.name}: {info.size_mb:.2f} MB")
            data: 0.08 MB

        Note:
            If the variable size exceeds warning_threshold_mb, a warning is logged.
            This helps identify memory-intensive variables during pipeline execution.
        """
        if not name:
            raise ValueError("Variable name cannot be empty")
        if value is None:
            raise ValueError(f"Cannot track None value for variable '{name}'")

        try:
            size_bytes = self.get_object_size(value)
        except Exception as e:
            raise RuntimeError(
                f"Failed to calculate memory size for variable '{name}' "
                f"of type {type(value).__name__}.\nOriginal error: {str(e)}"
            ) from e

        self._variable_sizes[name] = size_bytes

        info = VariableMemoryInfo(name=name, size_bytes=size_bytes, type_name=type(value).__name__)

        if self.config.log_memory_usage:
            logger.info(f"Variable '{name}' ({info.type_name}): {info.size_mb:.2f} MB")

        if info.size_mb > self.config.warning_threshold_mb:
            logger.warning(
                f"Variable '{name}' exceeds memory threshold: "
                f"{info.size_mb:.2f} MB > {self.config.warning_threshold_mb:.2f} MB"
            )

        return info

    def untrack_variable(self, name: str) -> None:
        """Stop tracking a variable and update cleared memory statistics.

        This method removes a variable from active tracking and adds its size
        to the cumulative total of cleared memory. It does not actually delete
        the variable from memory; that is handled by the MemoryManager.

        Args:
            name: The name of the variable to untrack.

        Example:
            >>> tracker = MemoryTracker()
            >>> tracker.track_variable("data", [1, 2, 3])
            >>> tracker.untrack_variable("data")
            >>> print(tracker.get_total_cleared_mb())
            0.0001  # Small amount for the list

        Note:
            If the variable is not currently tracked, this method does nothing.
        """
        if name in self._variable_sizes:
            self._total_cleared_bytes += self._variable_sizes[name]
            del self._variable_sizes[name]

    def get_total_memory_mb(self) -> float:
        """Calculate total memory used by all tracked variables.

        Returns:
            Total memory in megabytes (MB) across all tracked variables.

        Example:
            >>> tracker = MemoryTracker()
            >>> tracker.track_variable("data1", np.zeros(1000000))
            >>> tracker.track_variable("data2", np.zeros(1000000))
            >>> print(f"Total: {tracker.get_total_memory_mb():.2f} MB")
            Total: 15.26 MB
        """
        return sum(self._variable_sizes.values()) / (1024 * 1024)

    def get_total_cleared_mb(self) -> float:
        """Calculate total memory cleared since tracker initialization.

        Returns:
            Total cleared memory in megabytes (MB).

        Example:
            >>> tracker = MemoryTracker()
            >>> tracker.track_variable("data", np.zeros(1000000))
            >>> tracker.untrack_variable("data")
            >>> print(f"Cleared: {tracker.get_total_cleared_mb():.2f} MB")
            Cleared: 7.63 MB
        """
        return self._total_cleared_bytes / (1024 * 1024)

    def get_variable_info(self, name: str) -> Optional[VariableMemoryInfo]:
        """Get memory information for a specific variable.

        Args:
            name: The name of the variable to query.

        Returns:
            A VariableMemoryInfo object if the variable is tracked, None otherwise.

        Example:
            >>> tracker = MemoryTracker()
            >>> tracker.track_variable("data", [1, 2, 3])
            >>> info = tracker.get_variable_info("data")
            >>> if info:
            ...     print(f"{info.name}: {info.size_mb:.4f} MB")
            data: 0.0001 MB
        """
        if name not in self._variable_sizes:
            return None
        return VariableMemoryInfo(
            name=name, size_bytes=self._variable_sizes[name], type_name="unknown"
        )

    def get_all_variables_info(self) -> list[VariableMemoryInfo]:
        """Get memory information for all tracked variables.

        Returns:
            A list of VariableMemoryInfo objects, one for each tracked variable.

        Example:
            >>> tracker = MemoryTracker()
            >>> tracker.track_variable("data1", [1, 2, 3])
            >>> tracker.track_variable("data2", [4, 5, 6])
            >>> for info in tracker.get_all_variables_info():
            ...     print(f"{info.name}: {info.size_mb:.4f} MB")
            data1: 0.0001 MB
            data2: 0.0001 MB
        """
        return [
            VariableMemoryInfo(name=name, size_bytes=size, type_name="unknown")
            for name, size in self._variable_sizes.items()
        ]

    def log_summary(self) -> None:
        """Log a summary of memory usage statistics.

        This method outputs a formatted summary including:
        - Number of active variables
        - Total memory in use
        - Total memory cleared
        - Top 5 largest variables (if any exist)

        The summary is logged at INFO level.

        Example:
            >>> tracker = MemoryTracker(MemoryConfig(log_memory_usage=True))
            >>> tracker.track_variable("data1", np.zeros(1000000))
            >>> tracker.track_variable("data2", np.zeros(500000))
            >>> tracker.log_summary()
            # Logs:
            # Memory Summary:
            #   Active variables: 2
            #   Total memory in use: 11.44 MB
            #   Total memory cleared: 0.00 MB
            #   Top 5 largest variables:
            #     - data1: 7.63 MB
            #     - data2: 3.81 MB
        """
        total_mb = self.get_total_memory_mb()
        cleared_mb = self.get_total_cleared_mb()

        logger.info("Memory Summary:")
        logger.info(f"  Active variables: {len(self._variable_sizes)}")
        logger.info(f"  Total memory in use: {total_mb:.2f} MB")
        logger.info(f"  Total memory cleared: {cleared_mb:.2f} MB")

        if self._variable_sizes:
            logger.info("  Top 5 largest variables:")
            sorted_vars = sorted(self._variable_sizes.items(), key=lambda x: x[1], reverse=True)[:5]
            for name, size_bytes in sorted_vars:
                size_mb = size_bytes / (1024 * 1024)
                logger.info(f"    - {name}: {size_mb:.2f} MB")


class MemoryManager:
    """Manages memory tracking and automatic cleanup for pipeline variables.

    MemoryManager coordinates memory tracking and cleanup operations, providing
    high-level memory management for pipeline execution. It combines a MemoryTracker
    for monitoring with logic for determining when variables can be safely cleared.

    The manager supports:
    - Automatic cleanup of variables no longer needed by downstream stages
    - Manual variable clearing with garbage collection
    - Tracking of which variables have been cleared
    - Memory usage summaries and statistics

    Attributes:
        config: The memory configuration controlling management behavior.
        tracker: The MemoryTracker instance for monitoring variable sizes.
        _cleared_variables: Set of variable names that have been cleared.

    Example:
        >>> config = MemoryConfig(auto_clear_enabled=True)
        >>> manager = MemoryManager(config)
        >>> context_vars = {"data": large_dataframe}
        >>> # Check if variable can be cleared
        >>> if manager.can_clear_variable("data", {"stage1"}, {"stage1"}):
        ...     manager.clear_variable("data", context_vars)
    """

    def __init__(self, config: Optional[MemoryConfig] = None):
        """Initialize the memory manager.

        Args:
            config: Optional memory configuration. If None, uses default MemoryConfig.

        Example:
            >>> config = MemoryConfig(
            ...     auto_clear_enabled=True,
            ...     warning_threshold_mb=500.0
            ... )
            >>> manager = MemoryManager(config)
        """
        self.config = config or MemoryConfig()
        self.tracker = MemoryTracker(config)
        self._cleared_variables: Set[str] = set()

    def can_clear_variable(
        self, var_name: str, required_by: Set[str], completed_stages: Set[str]
    ) -> bool:
        """Determine if a variable can be safely cleared from memory.

        This method checks whether a variable is no longer needed by any downstream
        stages and can be cleared to free memory. A variable can be cleared if:
        1. Auto-clear is enabled in the configuration
        2. The variable has not already been cleared
        3. All stages that require the variable have completed

        Args:
            var_name: The name of the variable to check. Must be non-empty.
            required_by: Set of stage names that require this variable as input.
            completed_stages: Set of stage names that have finished execution.

        Returns:
            True if the variable can be safely cleared, False otherwise.

        Raises:
            ValueError: If var_name is empty.

        Example:
            >>> manager = MemoryManager(MemoryConfig(auto_clear_enabled=True))
            >>> # Variable needed by stage2, but only stage1 completed
            >>> can_clear = manager.can_clear_variable(
            ...     "data",
            ...     required_by={"stage1", "stage2"},
            ...     completed_stages={"stage1"}
            ... )
            >>> print(can_clear)
            False
            >>>
            >>> # All stages that need the variable have completed
            >>> can_clear = manager.can_clear_variable(
            ...     "data",
            ...     required_by={"stage1", "stage2"},
            ...     completed_stages={"stage1", "stage2", "stage3"}
            ... )
            >>> print(can_clear)
            True
        """
        if not var_name:
            raise ValueError("Variable name cannot be empty")

        if not self.config.auto_clear_enabled:
            return False

        if var_name in self._cleared_variables:
            return False

        for stage_name in required_by:
            if stage_name not in completed_stages:
                return False

        return True

    def clear_variable(self, var_name: str, context_variables: Dict[str, Any]) -> bool:
        """Clear a variable from memory and trigger garbage collection.

        This method removes a variable from the pipeline context, untracks it
        from memory monitoring, and triggers Python's garbage collector to
        reclaim the memory. It should be called when a variable is no longer
        needed by any downstream stages.

        Args:
            var_name: The name of the variable to clear. Must be non-empty.
            context_variables: The dictionary of context variables to modify.
                              This is typically the _variables dict from PipelineContext.

        Returns:
            True if the variable was successfully cleared, False if the variable
            was not found in the context.

        Raises:
            ValueError: If var_name is empty.
            RuntimeError: If clearing the variable fails. The original error is
                         included in the exception chain.

        Example:
            >>> manager = MemoryManager(MemoryConfig(log_memory_usage=True))
            >>> context_vars = {"data": large_dataframe, "config": {}}
            >>> manager.tracker.track_variable("data", large_dataframe)
            >>> success = manager.clear_variable("data", context_vars)
            >>> print(success)
            True
            >>> print("data" in context_vars)
            False

        Note:
            This method calls gc.collect() to immediately trigger garbage collection,
            which may cause a brief pause in execution. This ensures memory is
            reclaimed promptly rather than waiting for the next automatic GC cycle.
        """
        if not var_name:
            raise ValueError("Variable name cannot be empty")

        if var_name not in context_variables:
            return False

        try:
            self.tracker.untrack_variable(var_name)
            del context_variables[var_name]
            self._cleared_variables.add(var_name)

            gc.collect()

            if self.config.log_memory_usage:
                logger.info(f"Cleared variable '{var_name}' from memory")

            return True
        except Exception as e:
            raise RuntimeError(
                f"Failed to clear variable '{var_name}' from memory.\n" f"Original error: {str(e)}"
            ) from e

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of memory management statistics.

        Returns:
            A dictionary containing:
            - total_memory_mb: Total memory used by active variables (float)
            - total_cleared_mb: Total memory cleared since initialization (float)
            - active_variables: Number of variables currently tracked (int)
            - cleared_variables: Number of variables that have been cleared (int)

        Example:
            >>> manager = MemoryManager()
            >>> manager.tracker.track_variable("data", np.zeros(1000000))
            >>> summary = manager.get_summary()
            >>> print(f"Active: {summary['active_variables']}")
            Active: 1
            >>> print(f"Memory: {summary['total_memory_mb']:.2f} MB")
            Memory: 7.63 MB
        """
        return {
            "total_memory_mb": self.tracker.get_total_memory_mb(),
            "total_cleared_mb": self.tracker.get_total_cleared_mb(),
            "active_variables": len(self.tracker._variable_sizes),
            "cleared_variables": len(self._cleared_variables),
        }
