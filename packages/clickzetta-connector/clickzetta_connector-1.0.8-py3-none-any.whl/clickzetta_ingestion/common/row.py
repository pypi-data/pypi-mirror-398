from abc import ABC, abstractmethod
from typing import Any, List, Dict, Union, Optional, TypeVar, Tuple
import warnings
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class Row(ABC):
    """
    Row interface for setting values by column name or index.
    """

    @abstractmethod
    def set_value(self, column_name_or_index: Union[str, int], value: Any) -> None:
        """
        Set value to target column by name or index.

        Args:
            column_name_or_index: Column name (str) or column index (int)
            value: Value to set
        """
        pass

    def set_value_by_name(self, column_name: str, value: Any) -> None:
        """
        Set value to target column name.

        Args:
            column_name: Name of the column
            value: Value to set
        """
        self.set_value(column_name, value)

    def set_value_by_index(self, column_index: int, value: Any) -> None:
        """
        Set value to target column index. Column index must be original column index of schema.

        Args:
            column_index: Index of the column
            value: Value to set
        """
        self.set_value(column_index, value)

    def set_value_list(self, value_list: List[Tuple[Union[str, int], Any]]) -> None:
        """
        Set value list with pair<column_name, value> or pair<column_index, value>.

        Args:
            value_list: List of Pair objects containing column identifiers and values

        Raises:
            ValueError: If value_list is None
            TypeError: If pair type is not supported
        """
        if value_list is None:
            raise ValueError("value_list cannot be None")

        for pair in value_list:
            if isinstance(pair[0], str):
                self.set_value(pair[0], pair[1])
            elif isinstance(pair[0], int):
                self.set_value(pair[0], pair[1])
            else:
                raise TypeError(f"Not supported value_list pair type: {type(pair[0])}")

    def set_values_by_names(self, column_names: List[str], values: List[Any]) -> None:
        """
        Set values list with target column names & values.

        Args:
            column_names: List of column names
            values: List of values corresponding to column names

        Raises:
            ValueError: If column_names size doesn't equal values size
        """
        if len(column_names) != len(values):
            raise ValueError("column_names size must equal values size")

        for i in range(len(column_names)):
            self.set_value(column_names[i], values[i])

    def set_values_map(self, value_maps: Dict[Union[str, int], Any]) -> None:
        """
        Set values map with target column names|column indexes & values.

        Args:
            value_maps: Dictionary mapping column identifiers to values

        Raises:
            ValueError: If value_maps is None
            TypeError: If map key type is not supported
        """
        if value_maps is None:
            raise ValueError("value_maps cannot be None")

        for key, value in value_maps.items():
            if isinstance(key, str):
                self.set_value(key, value)
            elif isinstance(key, int):
                self.set_value(key, value)
            else:
                raise TypeError(f"Not supported map key type: {type(key)}")

    def get_write_operation(self) -> Optional[T]:
        """
        Return write operation which this row wraps.

        Returns:
            The write operation object

        Note:
            This method is deprecated
        """
        warnings.warn("get_write_operation is deprecated", DeprecationWarning, stacklevel=2)
        return None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the row to a dictionary representation.

        Returns:
            A dictionary with column names as keys and their corresponding values.
        """
        raise NotImplementedError("to_dict method must be implemented by subclasses")

    def from_dict(self, data: Dict[str, Any]):
        """Populate row from dictionary."""
        for column_name, value in data.items():
            try:
                self.set_value(column_name, value)
            except ValueError:
                # Skip unknown columns
                logger.warning(f"Skipping unknown column: {column_name}")
        return self