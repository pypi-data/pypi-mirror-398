# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.3] - 2025-12-24

### Changed

- Project folder structure
- Project metadata and configuration updates
- LoggingManager now uses a singleton pattern to ensure consistent configuration across multiple instances.
- LoggingManagerConfig now has a default constructor with sensible defaults.
- setup_logger() now returns the LoggingManager instance for easier configuration.
- PipelineDefinition now accepts an optional list of stages in the constructor.

## [0.1.2] - 2025

### Changed

- Updated project version to 0.1.2
- Modified contribution guidelines

## [0.1.1] - 2025

### Changed

- Updated Python version requirements
- Updated project dependencies

## [0.1.0] - 2025

### Added

- Initial release of stagecraft
- Pipeline architecture with declarative stages and conditions
- Type-safe variable system with support for DataFrames (`DFVar`), NumPy arrays (`NDArrayVar`), and serializable data (`SVar`)
- Built-in memory tracking and optimization for data-intensive workflows
- Data sources for CSV, JSON, and file-based data
- Flexible condition system for controlling stage execution:
  - `AlwaysExecute` for unconditional execution
  - `AndCondition` and `OrCondition` for combining conditions
  - `ConfigFlagCondition` for configuration-based execution
  - `VariableExistsCondition` for variable presence checks
  - `CustomCondition` for custom logic
- Comprehensive exception handling with custom wrappers
- Configurable logging system for pipeline monitoring
- Core components:
  - `PipelineDefinition` for defining pipeline structure
  - `PipelineRunner` for executing pipelines
  - `ETLStage` base class for custom stages
  - `PipelineContext` for managing pipeline state
- Utility functions for:
  - File operations (read, write, append)
  - String manipulation
  - Time operations
  - Web utilities
  - OS operations
  - CSV and JSON processing
- Dependencies: pandas>=2.0.0, numpy>=1.24.0, pandera>=0.17.0
- Python 3.9+ support
- Apache-2.0 license

[0.1.3]: https://github.com/alkndoom/stagecraft/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/alkndoom/stagecraft/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/alkndoom/stagecraft/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/alkndoom/stagecraft/releases/tag/v0.1.0
