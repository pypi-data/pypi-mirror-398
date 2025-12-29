from collections.abc import MutableMapping
from typing import Dict, Any, TypeVar, Iterator, Tuple, Optional

T = TypeVar('T')

class Configure(MutableMapping):
    """Configuration manager that provides type-safe access to properties."""
    
    def __init__(self, properties: Dict = None):
        self._properties = properties or {}

    def get(self, key: str, default: T = None) -> T:
        """Get a value with automatic type conversion based on default value type."""
        if default is None:
            return self._properties.get(key)
            
        return self._get_with_type(key, default)
        
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get a boolean value."""
        return self._get_with_type(key, default)
        
    def get_int(self, key: str, default: int = 0) -> int:
        """Get an integer value."""
        return self._get_with_type(key, default)
        
    def get_float(self, key: str, default: float = 0.0) -> float:
        """Get a float value."""
        return self._get_with_type(key, default)
        
    def get_str(self, key: str, default: str = "") -> str:
        """Get a string value."""
        return self._get_with_type(key, default)

    def get_properties(self, prefix: str = None,
                       key_prefix: str = None,
                       key_replace: str = None) -> Dict:
        if prefix is None:
            return self._properties
        return self.filter(prefix, (key_prefix, key_replace))

    def filter(self, prefix: str = None, replace_prefix: Optional[Tuple[str, str]] = None) -> Dict:
        """
        Get properties filtered by prefix with optional prefix replacement.
        
        Args:
            prefix: Filter properties starting with this prefix
            replace_prefix: Tuple of (old_prefix, new_prefix) to replace in keys
            
        Returns:
            Dict of filtered and optionally transformed properties
        """
        if not prefix:
            return self._properties.copy()
            
        result = {}
        for key, value in self._properties.items():
            if isinstance(key, str) and key.startswith(prefix):
                if replace_prefix:
                    old_prefix, new_prefix = replace_prefix
                    new_key = key.replace(old_prefix, new_prefix, 1)
                    result[new_key] = str(value)
                else:
                    result[key] = value
        return result

    def _get_with_type(self, key: str, default: T) -> T:
        """Get a value with type conversion based on default value type."""
        if key not in self._properties:
            return default
            
        value = self._properties[key]
        
        try:
            if isinstance(default, bool):
                if isinstance(value, str):
                    return value.lower() == 'true'
                return bool(value)
                
            if isinstance(default, int):
                return int(float(value))  # Handle both int and float strings
                
            if isinstance(default, float):
                return float(value)
                
            if isinstance(default, str):
                return str(value)
                
            return value
                
        except (ValueError, TypeError):
            return default

    # MutableMapping protocol implementation
    def __getitem__(self, key: str) -> Any:
        return self._properties[key]

    def __setitem__(self, key: str, value: Any):
        self._properties[key] = value

    def __delitem__(self, key: str):
        del self._properties[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._properties)

    def __len__(self) -> int:
        return len(self._properties)

    def __str__(self) -> str:
        return str(self._properties)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._properties})" 