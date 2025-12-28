import logging
from datetime import datetime
from typing import Any, Dict, Optional, Set

from .context import PipelineContext
from .definition import PipelineDefinition
from .memory import MemoryConfig
from .pipeline_metadata import (
    ExecutionStatus,
    PipelineExecutionMetadata,
    PipelineResult,
    StageExecutionMetadata,
)
from .stages import ETLStage

logger = logging.getLogger(__name__)


class PipelineRunner:
    def __init__(self, memory_config: Optional[MemoryConfig] = None):
        self.current_pipeline: Optional[PipelineDefinition] = None
        self.execution_metadata: Optional[PipelineExecutionMetadata] = None
        self.memory_config = memory_config or MemoryConfig()

    def __initialize_execution(self, pipeline: PipelineDefinition) -> None:
        """Initialize pipeline execution."""
        self.current_pipeline = pipeline
        self.execution_metadata = PipelineExecutionMetadata(
            pipeline_name=pipeline.name,
            start_time=datetime.now(),
            status=ExecutionStatus.RUNNING,
        )

        logger.info(f"Starting pipeline execution: {pipeline.name}")
        logger.info(f"Pipeline metadata: {pipeline.get_metadata()}")

    def __finalize_execution(self, success: bool, error: Exception = None) -> None:  # type: ignore
        """Finalize pipeline execution."""
        if self.execution_metadata:
            self.execution_metadata.end_time = datetime.now()
            self.execution_metadata.duration = (
                self.execution_metadata.end_time - self.execution_metadata.start_time
            ).total_seconds()

            if success:
                self.execution_metadata.status = ExecutionStatus.COMPLETED
                logger.info(
                    f"Pipeline completed successfully in {self.execution_metadata.duration:.2f} seconds"
                )
            else:
                self.execution_metadata.status = ExecutionStatus.FAILED
                self.execution_metadata.error = error
                logger.warning(
                    f"Pipeline failed after {self.execution_metadata.duration:.2f} seconds"
                )

    def run(self, pipeline: PipelineDefinition, initial_context: Dict[str, Any] = None) -> PipelineResult:  # type: ignore
        """
        Execute a complete ETL pipeline.

        Args:
            pipeline: Pipeline definition to execute

        Returns:
            Dictionary containing execution results and metadata
        """
        try:
            pipeline.validate(initial_context)
            self.__initialize_execution(pipeline)

            # Create pipeline context with memory management
            context = PipelineContext(initial_context, memory_config=self.memory_config)

            # Inject context into all stages
            for stage in pipeline.stages:
                stage.set_context(context)

            self.__execute_pipeline_stages(pipeline, context)

            # Log final memory summary
            if self.memory_config.enabled and self.memory_config.log_memory_usage:
                context.log_memory_summary()

            self.__finalize_execution(True)
            result = PipelineResult(success=True, metadata=self.execution_metadata)
            return result
        except Exception as e:
            self.__finalize_execution(False, e)
            result = PipelineResult(success=False, metadata=self.execution_metadata, error=e)
            return result

    def __build_variable_dependency_map(self, pipeline: PipelineDefinition) -> Dict[str, Set[str]]:
        """
        Build a map of which variables are required by which stages.

        Args:
            pipeline: Pipeline definition

        Returns:
            Dictionary mapping variable names to sets of stage names that require them
        """
        var_required_by: Dict[str, Set[str]] = {}

        for stage in pipeline.stages:
            for name in stage._input_keys:
                if name not in var_required_by:
                    var_required_by[name] = set()
                var_required_by[name].add(stage.name)

        return var_required_by

    def __log_stage_start(self, stage_index: int, total_stages: int, stage_name: str) -> None:
        """Log the start of stage execution."""
        logger.info(f"Executing stage {stage_index + 1}/{total_stages}: {stage_name}")

    def __record_stage_metadata(self, metadata: StageExecutionMetadata) -> None:
        """Record stage execution metadata to pipeline execution metadata."""
        if self.execution_metadata:
            self.execution_metadata.stages_executed.append(metadata)

    def __create_stage_metadata(
        self, stage_name: str, start_time: datetime, status: ExecutionStatus, error: Exception = None  # type: ignore
    ) -> StageExecutionMetadata:
        """Create stage execution metadata with calculated duration."""
        return StageExecutionMetadata(
            name=stage_name,
            duration=(datetime.now() - start_time).total_seconds(),
            status=status,
            error=error,
        )

    def __handle_skipped_stage(
        self, stage: ETLStage, start_time: datetime, completed_stages: Set[str]
    ) -> None:
        """Handle a stage that was skipped due to its execution condition."""
        skip_reason = stage.get_skip_reason()
        logger.info(f"Skipping stage '{stage.name}': {skip_reason}")

        metadata = self.__create_stage_metadata(stage.name, start_time, ExecutionStatus.SKIPPED)
        self.__record_stage_metadata(metadata)
        completed_stages.add(stage.name)

    def __handle_successful_stage(
        self, stage_name: str, start_time: datetime, completed_stages: Set[str]
    ) -> None:
        """Handle a stage that executed successfully."""
        metadata = self.__create_stage_metadata(stage_name, start_time, ExecutionStatus.COMPLETED)
        self.__record_stage_metadata(metadata)
        logger.info(f"Stage completed in {metadata.duration:.2f} seconds")
        completed_stages.add(stage_name)

    def __handle_failed_stage(
        self, stage_name: str, start_time: datetime, error: Exception
    ) -> None:
        """Handle a stage that failed during execution."""
        metadata = self.__create_stage_metadata(
            stage_name, start_time, ExecutionStatus.FAILED, error
        )
        self.__record_stage_metadata(metadata)

    def __auto_clear_memory_if_enabled(
        self,
        context: PipelineContext,
        var_required_by: Dict[str, Set[str]],
        completed_stages: Set[str],
    ) -> None:
        """Auto-clear unused variables from memory if memory management is enabled."""
        if self.memory_config.enabled and self.memory_config.auto_clear_enabled and context:
            cleared = context.auto_clear_unused_variables(var_required_by, completed_stages)
            if cleared > 0:
                logger.info(f"Auto-cleared {cleared} unused variable(s) from memory")

    def __execute_single_stage(
        self,
        stage: ETLStage,
        stage_index: int,
        total_stages: int,
        context: PipelineContext,
        var_required_by: Dict[str, Set[str]],
        completed_stages: Set[str],
    ) -> None:
        """Execute a single pipeline stage with error handling and metadata tracking."""
        self.__log_stage_start(stage_index, total_stages, stage.name)
        stage_start = datetime.now()

        try:
            if not stage.should_execute():
                self.__handle_skipped_stage(stage, stage_start, completed_stages)
                return

            stage.execute()
            self.__handle_successful_stage(stage.name, stage_start, completed_stages)
            self.__auto_clear_memory_if_enabled(context, var_required_by, completed_stages)

        except Exception as e:
            self.__handle_failed_stage(stage.name, stage_start, e)
            raise

    def __execute_pipeline_stages(self, pipeline: PipelineDefinition, context: PipelineContext):
        """Execute pipeline stages sequentially."""
        completed_stages: Set[str] = set()
        var_required_by = self.__build_variable_dependency_map(pipeline)

        for i, stage in enumerate(pipeline.stages):
            self.__execute_single_stage(
                stage,
                i,
                len(pipeline.stages),
                context,
                var_required_by,
                completed_stages,
            )

    def get_execution_summary(self) -> Optional[PipelineExecutionMetadata]:
        """Get summary of the last pipeline execution."""
        return self.execution_metadata
