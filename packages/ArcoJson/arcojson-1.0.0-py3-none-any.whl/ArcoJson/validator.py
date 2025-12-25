"""Data validation module for json2csv-pro."""

from typing import List, Dict, Any
from .exceptions import ValidationError


class DataValidator:
    """
    Validates JSON data before conversion.
    
    Example:
        >>> from json2csv_pro import DataValidator
        >>> validator = DataValidator()
        >>> data = [{"name": "John", "age": 30}]
        >>> validator.validate_data(data=data)
    """
    
    def validate_data(self, **kwargs) -> bool:
        """
        Validate JSON data structure.
        
        Args:
            **kwargs: Validation parameters
                - data (List[Dict]): Data to validate
                - strict (bool): Enable strict validation (default: False)
        
        Returns:
            bool: True if valid
        
        Raises:
            ValidationError: If validation fails
            
        Example:
            >>> validator = DataValidator()
            >>> data = [{"name": "John"}, {"name": "Jane"}]
            >>> validator.validate_data(data=data, strict=True)
        """
        data = kwargs.get('data')
        strict = kwargs.get('strict', False)
        
        if not isinstance(data, list):
            raise ValidationError("Data must be a list of dictionaries")
        
        if not data:
            raise ValidationError("Data cannot be empty")
        
        if not all(isinstance(item, dict) for item in data):
            raise ValidationError("All items must be dictionaries")
        
        if strict:
            self._validate_strict(data)
        
        return True
    
    def _validate_strict(self, data: List[Dict]) -> None:
        """Validate that all items have the same keys."""
        if not data:
            return
        
        first_keys = set(data[0].keys())
        for idx, item in enumerate(data[1:], 1):
            if set(item.keys()) != first_keys:
                raise ValidationError(
                    f"Item at index {idx} has different keys. "
                    f"Expected: {first_keys}, Got: {set(item.keys())}"
                )