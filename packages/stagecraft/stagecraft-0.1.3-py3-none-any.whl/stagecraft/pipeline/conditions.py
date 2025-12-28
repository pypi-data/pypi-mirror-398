"""
Conditional execution support for pipeline stages.

This module provides a flexible condition system that allows stages to be
conditionally executed based on runtime state, configuration, or previous results.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional

from .context import PipelineContext


class StageCondition(ABC):
    """
    Abstract base class for stage execution conditions.

    Conditions determine whether a stage should be executed or skipped.
    They are evaluated at runtime before stage execution.

    Example:
        ```python
        class MyStage(ETLStage):
            name = "my_stage"
            condition = InputNotEmptyCondition("input_data")

            input_data = sconsume(DFVar())
            output = sproduce(DFVar())

            def recipe(self):
                self.output = self.input_data.copy()
        ```
    """

    @abstractmethod
    def should_execute(self, context: PipelineContext, stage_name: str) -> bool:
        """
        Determine if the stage should execute.

        Args:
            context: Pipeline context with current variables
            stage_name: Name of the stage being evaluated

        Returns:
            True if stage should execute, False to skip
        """
        pass

    @abstractmethod
    def get_skip_reason(self) -> str:
        """
        Get human-readable reason for skipping.

        Returns:
            Description of why the stage was skipped
        """
        pass


class AlwaysExecute(StageCondition):
    """Condition that always executes (default behavior)."""

    def should_execute(self, context: PipelineContext, stage_name: str) -> bool:
        return True

    def get_skip_reason(self) -> str:
        return ""


class InputNotEmptyCondition(StageCondition):
    """
    Skip stage if input variable is empty.

    For DataFrames: checks if len(df) == 0
    For lists/tuples: checks if len(collection) == 0
    For other types: checks if value is None

    Example:
        ```python
        class ProcessData(ETLStage):
            name = "process_data"
            condition = InputNotEmptyCondition("input_data")

            input_data = sconsume(DFVar())
            output = sproduce(DFVar())

            def recipe(self):
                # Only runs if input_data is not empty
                self.output = self.input_data[self.input_data['value'] > 0]
        ```
    """

    def __init__(self, variable_name: str):
        self.variable_name = variable_name
        self._skip_reason = ""

    def should_execute(self, context: PipelineContext, stage_name: str) -> bool:
        if not context.has(self.variable_name):
            self._skip_reason = f"Input variable '{self.variable_name}' not found in context"
            return False

        value = context.get(self.variable_name)

        if value is None:
            self._skip_reason = f"Input variable '{self.variable_name}' is None"
            return False

        # Check if value is empty
        if hasattr(value, "__len__"):
            if len(value) == 0:
                self._skip_reason = f"Input variable '{self.variable_name}' is empty (length=0)"
                return False

        return True

    def get_skip_reason(self) -> str:
        return self._skip_reason


class ConfigFlagCondition(StageCondition):
    """
    Execute stage only if configuration flag is set.

    Example:
        ```python
        class OptionalStage(ETLStage):
            name = "optional_stage"
            condition = ConfigFlagCondition("enable_optional_processing")

            def recipe(self):
                # Only runs if config.enable_optional_processing is True
                pass
        ```
    """

    def __init__(self, config_key: str, config_dict: Optional[Dict[str, Any]] = None):
        self.config_key = config_key
        self.config_dict = config_dict or {}

    def should_execute(self, context: PipelineContext, stage_name: str) -> bool:
        return self.config_dict.get(self.config_key, False)

    def get_skip_reason(self) -> str:
        return f"Configuration flag '{self.config_key}' is not enabled"


class VariableExistsCondition(StageCondition):
    """
    Execute stage only if a variable exists in context.

    Example:
        ```python
        class ConditionalStage(ETLStage):
            name = "conditional_stage"
            condition = VariableExistsCondition("optional_input")

            optional_input = sconsume(DFVar())
            output = sproduce(DFVar())

            def recipe(self):
                # Only runs if optional_input exists
                self.output = self.optional_input.copy()
        ```
    """

    def __init__(self, variable_name: str):
        self.variable_name = variable_name

    def should_execute(self, context: PipelineContext, stage_name: str) -> bool:
        return context.has(self.variable_name)

    def get_skip_reason(self) -> str:
        return f"Variable '{self.variable_name}' does not exist in context"


class CustomCondition(StageCondition):
    """
    Execute stage based on custom function.

    Example:
        ```python
        def check_business_hours(context, stage_name):
            from datetime import datetime
            hour = datetime.now().hour
            return 9 <= hour <= 17

        class BusinessHoursStage(ETLStage):
            name = "business_hours_stage"
            condition = CustomCondition(
                check_business_hours,
                skip_reason="Outside business hours (9 AM - 5 PM)"
            )

            def recipe(self):
                # Only runs during business hours
                pass
        ```
    """

    def __init__(
        self,
        condition_fn: Callable[[PipelineContext, str], bool],
        skip_reason: str = "Custom condition not met",
    ):
        self.condition_fn = condition_fn
        self.skip_reason = skip_reason

    def should_execute(self, context: PipelineContext, stage_name: str) -> bool:
        try:
            return self.condition_fn(context, stage_name)
        except Exception:
            return False

    def get_skip_reason(self) -> str:
        return self.skip_reason


class AndCondition(StageCondition):
    """
    Execute stage only if ALL conditions are met.

    Example:
        ```python
        class MultiConditionStage(ETLStage):
            name = "multi_condition"
            condition = AndCondition([
                InputNotEmptyCondition("input_data"),
                ConfigFlagCondition("enable_processing")
            ])

            def recipe(self):
                # Only runs if input is not empty AND config flag is set
                pass
        ```
    """

    def __init__(self, conditions: list[StageCondition]):
        self.conditions = conditions
        self._failed_condition: Optional[StageCondition] = None

    def should_execute(self, context: PipelineContext, stage_name: str) -> bool:
        for condition in self.conditions:
            if not condition.should_execute(context, stage_name):
                self._failed_condition = condition
                return False
        return True

    def get_skip_reason(self) -> str:
        if self._failed_condition:
            return self._failed_condition.get_skip_reason()
        return "One or more conditions not met"


class OrCondition(StageCondition):
    """
    Execute stage if ANY condition is met.

    Example:
        ```python
        class FlexibleStage(ETLStage):
            name = "flexible"
            condition = OrCondition([
                VariableExistsCondition("input_a"),
                VariableExistsCondition("input_b")
            ])

            def recipe(self):
                # Runs if either input_a OR input_b exists
                pass
        ```
    """

    def __init__(self, conditions: list[StageCondition]):
        self.conditions = conditions

    def should_execute(self, context: PipelineContext, stage_name: str) -> bool:
        return any(condition.should_execute(context, stage_name) for condition in self.conditions)

    def get_skip_reason(self) -> str:
        return "None of the conditions were met"
