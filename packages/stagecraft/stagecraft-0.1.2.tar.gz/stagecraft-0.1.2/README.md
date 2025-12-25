# stagecraft

A Python library for building robust ETL (Extract, Transform, Load) pipelines with declarative stages and powerful data flow management.

## Features

- **Pipeline Architecture**: Build complex data pipelines using declarative stages and conditions
- **Type-Safe Variables**: Strongly-typed variable system with support for DataFrames, NumPy arrays, and serializable data
- **Memory Management**: Built-in memory tracking and optimization for data-intensive workflows
- **Data Sources**: Out-of-the-box support for CSV, JSON, and file-based data sources
- **Conditional Execution**: Flexible condition system for controlling stage execution
- **Exception Handling**: Comprehensive exception handling with custom wrappers
- **Logging**: Configurable logging system for pipeline monitoring
- **Utility Functions**: Rich set of utility functions for file operations, string manipulation, and more

## Installation

```bash
pip install stagecraft
```

## Quick Start

```python
from stagecraft import (
    PipelineDefinition,
    PipelineRunner,
    ETLStage,
    DFVar,
)

# Define your pipeline stages
class LoadDataStage(ETLStage):
    def recipe(self, **kwargs):
        # Load your data
        pass

# Create pipeline definition
pipeline = PipelineDefinition(
    name="my_pipeline",
    stages=[LoadDataStage()]
)

# Run the pipeline
runner = PipelineRunner(pipeline)
result = runner.run()
```

## Core Components

### Pipeline System

- `PipelineDefinition`: Define pipeline structure and stages
- `PipelineRunner`: Execute pipelines with context management
- `ETLStage`: Base class for creating custom pipeline stages
- `PipelineContext`: Manage pipeline state and variables

### Variables

- `DFVar`: pandas DataFrame variables
- `NDArrayVar`: NumPy array variables
- `SVar`: Serializable variables for general Python objects

### Data Sources

- `CSVSource`: Read data from CSV files
- `JSONSource`: Read data from JSON files
- `FileSource`: Read data from text files

### Conditions

- `AlwaysExecute`: Unconditional execution
- `AndCondition`/`OrCondition`: Combine multiple conditions
- `ConfigFlagCondition`: Execute based on configuration flags
- `VariableExistsCondition`: Check variable presence
- `CustomCondition`: Define custom execution logic

### Utilities

- File operations: `read_file`, `write_file`, `append_file`
- CSV operations: `read_csv`, `write_csv`, `append_csv`
- JSON operations: `read_json`, `write_json`, `append_json`
- String utilities: `camel_to_snake_case`, `snake_to_camel_case`, and more
- Time utilities: `get_timestamp`, `get_current_date`

## Requirements

- Python 3.8+

## Development

Install development dependencies:

```bash
pip install stagecraft[dev]
```

Run tests:

```bash
pytest
```

## License

Apache-2.0 License - see LICENSE file for details

## Contributing

This project is not accepting contributions at this time.
