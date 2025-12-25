"""Custom exceptions for json2csv-pro library."""


class JSON2CSVError(Exception):
    """Base exception for all json2csv-pro errors."""
    pass


class ValidationError(JSON2CSVError):
    """Raised when data validation fails."""
    pass


class ConversionError(JSON2CSVError):
    """Raised when conversion process fails."""
    pass


class FileNotFoundError(JSON2CSVError):
    """Raised when specified file is not found."""
    pass