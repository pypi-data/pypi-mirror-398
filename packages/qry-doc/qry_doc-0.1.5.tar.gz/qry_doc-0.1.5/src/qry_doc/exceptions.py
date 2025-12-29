"""
Custom exceptions for qry-doc library.

This module defines a hierarchy of exceptions that provide user-friendly
error messages while preserving internal error details for debugging.
"""
from typing import Optional


class QryDocError(Exception):
    """
    Base exception for all qry-doc errors.
    
    Attributes:
        user_message: A user-friendly message suitable for display.
        internal_error: The original exception that caused this error (if any).
    """
    
    def __init__(
        self,
        user_message: str,
        internal_error: Optional[Exception] = None
    ) -> None:
        self.user_message = user_message
        self.internal_error = internal_error
        super().__init__(user_message)
    
    def __str__(self) -> str:
        return self.user_message


class QueryError(QryDocError):
    """
    Raised when a natural language query cannot be interpreted or executed.
    
    Examples:
        - Query syntax is ambiguous
        - LLM fails to generate valid code
        - Generated code execution fails
    """
    pass


class ExportError(QryDocError):
    """
    Raised when data export operations fail.
    
    Examples:
        - Query returns non-tabular data for CSV export
        - File write permission denied
        - Invalid output path
    """
    pass


class ReportError(QryDocError):
    """
    Raised when PDF report generation fails.
    
    Examples:
        - Chart rendering fails
        - Template configuration invalid
        - PDF write error
    """
    pass


class DataSourceError(QryDocError):
    """
    Raised when data source loading fails.
    
    Examples:
        - Invalid file path
        - Unsupported data format
        - Database connection failure
    """
    pass


class ValidationError(QryDocError):
    """
    Raised when output validation fails.
    
    Examples:
        - Generated code contains unsafe operations
        - DataFrame is empty or malformed
        - Chart file is missing or corrupt
    """
    pass
