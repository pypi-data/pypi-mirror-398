"""Pipeline definition for building and validating multi-stage ETL workflows.

This module provides the PipelineDefinition class, which serves as a builder and
container for ETL pipelines. It manages the sequential composition of stages,
validates dependencies between stages, and ensures data flow integrity throughout
the pipeline execution.

A pipeline definition is responsible for:
- Maintaining an ordered list of ETL stages
- Validating that each stage's input dependencies are satisfied
- Preventing duplicate stage names
- Providing metadata about the pipeline structure
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .pipeline_metadata import PipelineMetadata
from .stages import ETLStage


class PipelineDefinition:
    """Builder and validator for multi-stage ETL pipelines.

    PipelineDefinition provides a fluent interface for constructing pipelines by
    adding stages sequentially. It validates that the data flow between stages is
    correct, ensuring that each stage's required inputs are either:
    1. Produced by a previous stage's outputs
    2. Available in the initial context
    3. Loadable from a configured data source

    The class enforces several constraints:
    - Each stage must have a unique name within the pipeline
    - All stage input dependencies must be resolvable
    - Stages must be valid ETLStage instances

    Attributes:
        name: The name of the pipeline, used for identification and logging.
        stages: Ordered list of ETL stages that comprise the pipeline.

    Example:
        >>> pipeline = PipelineDefinition("data_processing")
        >>> pipeline.add_stage(LoadDataStage())
        >>> pipeline.add_stage(TransformStage())
        >>> pipeline.add_stage(SaveResultsStage())
        >>> pipeline.validate()
        True
    """

    def __init__(self, name: str, stages: Optional[List[ETLStage]] = None):
        """Initialize a new pipeline definition.

        Args:
            name: A descriptive name for the pipeline. Used for logging,
                 error messages, and metadata tracking.
            stages: Optional list of ETL stages to initialize the pipeline with.

        Example:
            >>> pipeline = PipelineDefinition("transaction_classification")
            >>> print(pipeline.name)
            'transaction_classification'
        """
        self.name = name
        self.stages: List[ETLStage] = []

        if stages:
            for stage in stages:
                self.add_stage(stage)

    def add_stage(self, stage: ETLStage) -> PipelineDefinition:
        """Add a stage to the pipeline with validation.

        This method appends a stage to the pipeline's execution sequence and
        performs several validation checks to ensure pipeline integrity:
        - The stage must be a valid ETLStage instance
        - The stage must have a non-empty name
        - The stage name must be unique within the pipeline

        The method supports method chaining for fluent pipeline construction.

        Args:
            stage: An ETLStage instance to add to the pipeline. Must be properly
                  configured with a unique name.

        Returns:
            Self, to enable method chaining for fluent pipeline construction.

        Raises:
            ValueError: If stage is None, has no name, or has a duplicate name.
            TypeError: If stage is not an instance of ETLStage.

        Example:
            >>> pipeline = PipelineDefinition("my_pipeline")
            >>> pipeline.add_stage(ExtractStage()).add_stage(TransformStage())
            >>> len(pipeline.stages)
            2
            >>>
            >>> # This will raise ValueError (duplicate name)
            >>> pipeline.add_stage(ExtractStage())  # Same name as first stage
        """
        if stage is None:
            raise ValueError("Cannot add None as a stage to the pipeline")
        if not isinstance(stage, ETLStage):
            raise TypeError(
                f"Stage must be an instance of ETLStage, got {type(stage).__name__}. "
                f"Ensure your stage class inherits from ETLStage."
            )
        if not hasattr(stage, "name") or not stage.name:
            raise ValueError(
                f"Stage {type(stage).__name__} must have a non-empty 'name' attribute. "
                f"Add 'name = \"your_stage_name\"' to your stage class."
            )

        existing_names = [s.name for s in self.stages]
        if stage.name in existing_names:
            raise ValueError(
                f"Stage with name '{stage.name}' already exists in pipeline '{self.name}'. "
                f"Each stage must have a unique name. Existing stages: {existing_names}"
            )

        self.stages.append(stage)
        return self

    def validate(self, initial_context: Optional[Dict[str, Any]] = None) -> bool:
        """Validate the pipeline definition and data flow integrity.

        This method performs comprehensive validation of the pipeline to ensure
        it can execute successfully. It checks that all stage input dependencies
        can be satisfied either by:
        1. Variables in the initial context
        2. Outputs from previous stages
        3. Loadable data sources configured on the stage

        Validation should be called after all stages have been added and before
        pipeline execution to catch configuration errors early.

        Args:
            initial_context: Optional dictionary of initial context variables that
                           will be available when the pipeline starts. Keys are
                           variable names, values are the initial data. This is
                           useful for providing configuration or seed data.

        Returns:
            True if all validation checks pass.

        Raises:
            ValueError: If any stage has input dependencies that cannot be satisfied.
                       The error message will indicate which stage and which input
                       is missing, along with available variables.

        Example:
            >>> pipeline = PipelineDefinition("my_pipeline")
            >>> pipeline.add_stage(LoadStage())
            >>> pipeline.add_stage(ProcessStage())
            >>> pipeline.validate()
            True
            >>>
            >>> # With initial context
            >>> pipeline.validate(initial_context={"config": {"param": 1}})
            True
            >>>
            >>> # This will raise ValueError if dependencies are missing
            >>> broken_pipeline = PipelineDefinition("broken")
            >>> broken_pipeline.add_stage(ProcessStage())  # Needs input from LoadStage
            >>> broken_pipeline.validate()  # Raises ValueError
        """
        self.__validate_dependencies(initial_context)
        return True

    def __validate_dependencies(self, initial_context: Optional[Dict[str, Any]] = None) -> bool:
        """Validate that each stage's input dependencies can be satisfied.

        This internal method performs a sequential walk through all stages,
        tracking which variables are available at each point. For each stage,
        it verifies that all required inputs are either:
        1. Already available from previous stages or initial context
        2. Can be loaded from a configured data source

        The method simulates the data flow through the pipeline without actually
        executing any stages, building up the set of available variables as it
        processes each stage's outputs.

        Args:
            initial_context: Optional dictionary of initial variables available
                           at pipeline start. If None, starts with an empty set.

        Returns:
            True if all dependencies are satisfied.

        Raises:
            ValueError: If any stage has an input that cannot be satisfied.
                       The error includes the stage name, missing input name,
                       and list of available variables for debugging.

        Note:
            This is a private method called by validate(). It should not be
            called directly by external code.
        """

        available_vars = set(initial_context.keys()) if initial_context else set()

        for stage in self.stages:
            for name in stage._input_keys:
                var = stage._vars.get(name)
                has_loadable_source = var.source is not None and var.source.load_enabled  # type: ignore
                if name not in available_vars and not has_loadable_source:
                    raise ValueError(
                        f"Stage '{stage.name}' requires input '{name}' "
                        f"which is not available. Available: {list(available_vars)}"
                    )

            for name in stage._output_keys:
                available_vars.add(name)
        return True

    def get_metadata(self) -> PipelineMetadata:
        """Generate metadata describing the pipeline structure.

        This method collects metadata from all stages in the pipeline and
        assembles it into a PipelineMetadata object. The metadata includes
        information about the pipeline name, stage sequence, and each stage's
        configuration.

        Metadata is useful for:
        - Documenting pipeline structure
        - Generating execution reports
        - Debugging and monitoring
        - Serializing pipeline definitions

        Returns:
            A PipelineMetadata object containing the pipeline name and a list
            of stage metadata objects.

        Example:
            >>> pipeline = PipelineDefinition("data_pipeline")
            >>> pipeline.add_stage(ExtractStage()).add_stage(TransformStage())
            >>> metadata = pipeline.get_metadata()
            >>> print(metadata.name)
            'data_pipeline'
            >>> print(len(metadata.stages))
            2
        """
        stages = [stage.get_metadata() for stage in self.stages]
        return PipelineMetadata(name=self.name, stages=stages)

    def __str__(self):
        """Return a string representation of the pipeline definition.

        Returns:
            A string showing the pipeline name and list of stages.

        Example:
            >>> pipeline = PipelineDefinition("my_pipeline")
            >>> pipeline.add_stage(ExtractStage())
            >>> str(pipeline)
            "PipelineDefinition(my_pipeline, [ExtractStage(...)])"
        """
        return f"PipelineDefinition({self.name}, {self.stages})"

    def __repr__(self):
        """Return a detailed string representation of the pipeline definition.

        Returns:
            Same as __str__() for this class.
        """
        return self.__str__()
