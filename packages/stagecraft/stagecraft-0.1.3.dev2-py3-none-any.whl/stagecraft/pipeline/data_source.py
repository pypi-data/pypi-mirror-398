"""Data source abstractions for pipeline stage input/output operations.

This module provides a hierarchy of data source classes that enable pipeline stages
to load input data and save output data in various formats. Each data source supports
configurable read/write modes to control whether loading, saving, or both operations
are permitted.

The module includes support for:
- CSV files (pandas DataFrames)
- JSON files (dictionaries)
- Text files (strings)
- NumPy arrays (.npy files)
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Literal

import numpy as np
import pandas as pd

from ..core.csv import read_csv, write_csv
from ..core.file import read_file, write_file
from ..core.json import read_json, write_json


class DataSource(ABC):
    """Abstract base class for all data sources in pipeline stages.

    DataSource defines the interface for loading and saving data in pipeline stages.
    Subclasses must implement the load() and save() methods for specific data formats.

    The mode parameter controls whether the data source can be read from, written to,
    or both. This is useful for preventing accidental overwrites or reads from
    write-only sources.

    Attributes:
        load_enabled: True if loading is permitted based on the mode.
        save_enabled: True if saving is permitted based on the mode.
    """

    def __init__(self, *, mode: Literal["r", "w", "w+"] = "w+"):
        """Initialize the data source with a specified access mode.

        Args:
            mode: Access mode for the data source:
                - "r": Read-only mode (load_enabled=True, save_enabled=False)
                - "w": Write-only mode (load_enabled=False, save_enabled=True)
                - "w+": Read-write mode (load_enabled=True, save_enabled=True)
                Default is "w+" to allow both operations.

        Example:
            >>> source = ConcreteDataSource(mode="r")  # Read-only
            >>> source.load_enabled
            True
            >>> source.save_enabled
            False
        """
        self.load_enabled = mode in ["r", "w+"]
        self.save_enabled = mode in ["w", "w+"]

    @abstractmethod
    def load(self) -> Any:
        """Load data from the source.

        This method must be implemented by subclasses to define how data is
        loaded from the specific source type.

        Returns:
            The loaded data. The type depends on the specific data source
            implementation (e.g., DataFrame, dict, str, ndarray).

        Raises:
            ValueError: If loading is not enabled for this data source.
            NotImplementedError: If called on the abstract base class.
        """
        pass

    @abstractmethod
    def save(self, value: Any):
        """Save data to the source.

        This method must be implemented by subclasses to define how data is
        saved to the specific source type.

        Args:
            value: The data to save. The expected type depends on the specific
                  data source implementation.

        Raises:
            ValueError: If saving is not enabled for this data source.
            NotImplementedError: If called on the abstract base class.
        """
        pass

    def __str__(self):
        """Return a string representation of the data source.

        Returns:
            A string showing the class name.
        """
        return f"{self.__class__.__name__}()"

    def __repr__(self):
        """Return a detailed string representation of the data source.

        Returns:
            Same as __str__() for the base class.
        """
        return self.__str__()


class _BaseFileSource(DataSource):
    """Base class for file-based data sources.

    This internal base class extends DataSource to add file path management
    for all file-based data sources. It should not be instantiated directly;
    use one of the concrete subclasses instead.

    Attributes:
        path: The file system path to the data file.
        load_enabled: Inherited from DataSource.
        save_enabled: Inherited from DataSource.
    """

    def __init__(self, path: str, /, *, mode: Literal["r", "w", "w+"] = "w+"):
        """Initialize the file-based data source.

        Args:
            path: File system path to the data file. Can be absolute or relative.
            mode: Access mode for the data source ("r", "w", or "w+").
                 See DataSource.__init__ for details.

        Example:
            >>> source = CSVSource("data/output.csv", mode="w")
            >>> source.path
            'data/output.csv'
        """
        super().__init__(mode=mode)
        self.path = path

    def __str__(self):
        """Return a string representation including the file path.

        Returns:
            A string showing the class name and file path.
        """
        return f"{self.__class__.__name__}({self.path})"


class CSVSource(_BaseFileSource):
    """Data source for CSV files containing tabular data.

    CSVSource handles loading and saving pandas DataFrames from/to CSV files.
    It uses the core CSV utilities which provide consistent formatting and
    error handling across the application.

    This is the recommended data source for tabular data in pipeline stages.

    Example:
        >>> # Read-write mode (default)
        >>> source = CSVSource("data/transactions.csv")
        >>> df = source.load()
        >>> processed_df = process(df)
        >>> source.save(processed_df)
        >>>
        >>> # Write-only mode
        >>> output = CSVSource("data/results.csv", mode="w")
        >>> output.save(results_df)
    """

    def load(self) -> pd.DataFrame:
        """Load a pandas DataFrame from the CSV file.

        Returns:
            A pandas DataFrame containing the data from the CSV file.

        Raises:
            ValueError: If loading is not enabled (mode is "w").
            FileNotFoundError: If the CSV file does not exist.
            pd.errors.ParserError: If the CSV file is malformed.

        Example:
            >>> source = CSVSource("data/input.csv", mode="r")
            >>> df = source.load()
            >>> print(df.shape)
            (1000, 5)
        """
        if not self.load_enabled:
            raise ValueError(f"Loading is not enabled for {self}")
        return read_csv(self.path)

    def save(self, value: pd.DataFrame):
        """Save a pandas DataFrame to the CSV file.

        Args:
            value: The DataFrame to save. Must be a valid pandas DataFrame.

        Note:
            If saving is not enabled (mode is "r"), this method silently
            does nothing rather than raising an error.

        Example:
            >>> source = CSVSource("data/output.csv", mode="w")
            >>> df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
            >>> source.save(df)
        """
        if self.save_enabled:
            write_csv(value, self.path)


class JSONSource(_BaseFileSource):
    """Data source for JSON files containing structured data.

    JSONSource handles loading and saving Python dictionaries from/to JSON files.
    It uses the core JSON utilities which provide consistent serialization and
    deserialization across the application.

    This is the recommended data source for configuration data, metadata, or
    any structured data that needs to be human-readable.

    Example:
        >>> # Load configuration
        >>> config_source = JSONSource("config/model_params.json", mode="r")
        >>> params = config_source.load()
        >>> print(params["learning_rate"])
        0.001
        >>>
        >>> # Save results
        >>> results_source = JSONSource("output/metrics.json", mode="w")
        >>> results_source.save({"accuracy": 0.95, "f1": 0.93})
    """

    def load(self) -> Dict[str, Any]:
        """Load a dictionary from the JSON file.

        Returns:
            A dictionary containing the data from the JSON file.

        Raises:
            ValueError: If loading is not enabled (mode is "w").
            FileNotFoundError: If the JSON file does not exist.
            json.JSONDecodeError: If the JSON file is malformed.

        Example:
            >>> source = JSONSource("data/config.json", mode="r")
            >>> config = source.load()
            >>> print(config.keys())
            dict_keys(['model', 'training', 'evaluation'])
        """
        if not self.load_enabled:
            raise ValueError(f"Loading is not enabled for {self}")
        return read_json(self.path)

    def save(self, value: Dict[str, Any]):
        """Save a dictionary to the JSON file.

        Args:
            value: The dictionary to save. Must be JSON-serializable.

        Note:
            If saving is not enabled (mode is "r"), this method silently
            does nothing rather than raising an error.

        Example:
            >>> source = JSONSource("data/output.json", mode="w")
            >>> data = {"status": "complete", "count": 42}
            >>> source.save(data)
        """
        if self.save_enabled:
            write_json(value, self.path)


class FileSource(_BaseFileSource):
    """Data source for plain text files.

    FileSource handles loading and saving text data from/to files. It reads
    the entire file content as a string and can save any value by converting
    it to a string representation.

    This is useful for:
    - Plain text data
    - Log files
    - Template files
    - Any data that can be represented as text

    Example:
        >>> # Read a text file
        >>> source = FileSource("data/template.txt", mode="r")
        >>> template = source.load()
        >>> print(template[:50])
        'Dear {name}, your account balance is {balance}...'
        >>>
        >>> # Write a report
        >>> report_source = FileSource("output/report.txt", mode="w")
        >>> report_source.save("Analysis complete. Total: 1000 records.")
    """

    def load(self) -> str:
        """Load the entire file content as a string.

        Returns:
            A string containing the complete file content.

        Raises:
            ValueError: If loading is not enabled (mode is "w").
            FileNotFoundError: If the file does not exist.
            UnicodeDecodeError: If the file cannot be decoded as text.

        Example:
            >>> source = FileSource("data/notes.txt", mode="r")
            >>> content = source.load()
            >>> print(len(content))
            1523
        """
        if not self.load_enabled:
            raise ValueError(f"Loading is not enabled for {self}")
        return read_file(self.path)

    def save(self, value: Any):
        """Save data to the file as text.

        The value is converted to a string using str() before writing.
        This allows saving any object that has a string representation.

        Args:
            value: The data to save. Will be converted to string if not already.

        Note:
            If saving is not enabled (mode is "r"), this method silently
            does nothing rather than raising an error.

        Example:
            >>> source = FileSource("output/log.txt", mode="w")
            >>> source.save("Process completed successfully")
            >>>
            >>> # Can save any object with __str__
            >>> source.save({"status": "done"})  # Saves string representation
        """
        if self.save_enabled:
            write_file(str(value), self.path)


class ArraySource(_BaseFileSource):
    """Data source for NumPy arrays stored in .npy files.

    ArraySource handles loading and saving NumPy arrays using NumPy's native
    binary format (.npy). This format is efficient for numerical data and
    preserves array metadata like dtype and shape.

    This is the recommended data source for:
    - Numerical arrays (vectors, matrices, tensors)
    - Model weights and embeddings
    - Preprocessed numerical features
    - Any data that benefits from NumPy's efficient binary format

    Example:
        >>> # Save embeddings
        >>> embeddings_source = ArraySource("data/embeddings.npy", mode="w")
        >>> embeddings = np.random.rand(1000, 128)
        >>> embeddings_source.save(embeddings)
        >>>
        >>> # Load for inference
        >>> source = ArraySource("data/embeddings.npy", mode="r")
        >>> loaded_embeddings = source.load()
        >>> print(loaded_embeddings.shape)
        (1000, 128)
    """

    def load(self) -> Any:
        """Load a NumPy array from the .npy file.

        Returns:
            A NumPy array or other object stored in the .npy file.
            The exact type depends on what was saved.

        Raises:
            ValueError: If loading is not enabled (mode is "w").
            FileNotFoundError: If the .npy file does not exist.
            IOError: If the file is not a valid .npy file.

        Example:
            >>> source = ArraySource("data/features.npy", mode="r")
            >>> features = source.load()
            >>> print(features.dtype, features.shape)
            float64 (500, 10)
        """
        if not self.load_enabled:
            raise ValueError(f"Loading is not enabled for {self}")
        return np.load(self.path)

    def save(self, value: Any):
        """Save a NumPy array to the .npy file.

        Args:
            value: The NumPy array or array-like object to save.
                  Can be any object that NumPy can serialize.

        Note:
            If saving is not enabled (mode is "r"), this method silently
            does nothing rather than raising an error.

        Example:
            >>> source = ArraySource("data/weights.npy", mode="w")
            >>> weights = np.array([[1.0, 2.0], [3.0, 4.0]])
            >>> source.save(weights)
            >>>
            >>> # Can also save structured arrays
            >>> structured = np.array([(1, 2.0), (3, 4.0)],
            ...                       dtype=[('id', 'i4'), ('value', 'f8')])
            >>> source.save(structured)
        """
        if self.save_enabled:
            np.save(self.path, value)
