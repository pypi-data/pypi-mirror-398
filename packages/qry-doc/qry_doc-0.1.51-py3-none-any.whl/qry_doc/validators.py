"""
Output validation and sanitization utilities for qry-doc.

This module provides validation for AI-generated outputs and sanitization
of error messages to prevent exposure of sensitive information.
"""
import re
from typing import Any, Optional
from pathlib import Path

import pandas as pd


class OutputValidator:
    """
    Validates and sanitizes outputs from AI operations.
    
    Provides methods to:
    - Validate DataFrames before export or rendering
    - Sanitize error messages to remove sensitive data
    - Verify file existence and readability
    """
    
    # Patterns that indicate sensitive data
    SENSITIVE_PATTERNS: list[re.Pattern[str]] = [
        # API keys (OpenAI, Anthropic, etc.)
        re.compile(r"sk-[a-zA-Z0-9\-_]{20,}", re.IGNORECASE),
        re.compile(r"sk-proj-[a-zA-Z0-9\-_]+", re.IGNORECASE),
        re.compile(r"api[_-]?key\s*[=:]\s*['\"]?[\w\-]+['\"]?", re.IGNORECASE),
        re.compile(r"OPENAI_API_KEY\s*=\s*[\w\-]+", re.IGNORECASE),
        re.compile(r"ANTHROPIC_API_KEY\s*=\s*[\w\-]+", re.IGNORECASE),
        
        # Database connection strings - redact entire connection string
        re.compile(r"(postgresql|mysql|mongodb|redis|sqlite)://[^\s]+", re.IGNORECASE),
        re.compile(r"password\s*[=:]\s*['\"]?[^\s'\"]+['\"]?", re.IGNORECASE),
        
        # Bearer tokens
        re.compile(r"Bearer\s+[a-zA-Z0-9\-_\.]+", re.IGNORECASE),
        
        # Generic secrets
        re.compile(r"secret\s*[=:]\s*['\"]?[\w\-]+['\"]?", re.IGNORECASE),
    ]
    
    # Replacement text for sensitive data
    REDACTED = "[REDACTED]"
    
    @classmethod
    def validate_dataframe(cls, data: Any) -> tuple[bool, str]:
        """
        Validate that data is a valid, non-empty DataFrame.
        
        Args:
            data: The data to validate.
            
        Returns:
            A tuple of (is_valid, error_message).
            If valid, error_message is empty string.
        """
        if data is None:
            return False, "El resultado es None. La consulta no retornó datos."
        
        if not isinstance(data, pd.DataFrame):
            return False, f"El resultado no es tabular (tipo: {type(data).__name__}). Reformule la consulta para obtener datos en formato de tabla."
        
        if data.empty:
            return False, "El DataFrame está vacío. La consulta no encontró datos que coincidan."
        
        # Check for completely null columns
        null_cols = data.columns[data.isnull().all()].tolist()
        if null_cols:
            return False, f"Las columnas {null_cols} contienen solo valores nulos."
        
        return True, ""
    
    @classmethod
    def sanitize_error_message(
        cls,
        error: Exception,
        additional_patterns: Optional[list[str]] = None
    ) -> str:
        """
        Remove sensitive information from error messages.
        
        Args:
            error: The exception to sanitize.
            additional_patterns: Extra patterns to redact (e.g., specific API keys).
            
        Returns:
            A sanitized error message safe for user display.
        """
        message = str(error)
        
        # Remove sensitive patterns
        for pattern in cls.SENSITIVE_PATTERNS:
            message = pattern.sub(cls.REDACTED, message)
        
        # Remove additional custom patterns
        if additional_patterns:
            for pattern_str in additional_patterns:
                try:
                    # Escape special regex characters in the pattern
                    escaped = re.escape(pattern_str)
                    message = re.sub(escaped, cls.REDACTED, message, flags=re.IGNORECASE)
                except re.error:
                    # If pattern is invalid, skip it
                    continue
        
        # Remove file paths that might reveal system structure
        # Keep only the filename, not the full path
        message = re.sub(
            r"(/[a-zA-Z0-9_\-./]+)+/([a-zA-Z0-9_\-]+\.[a-zA-Z0-9]+)",
            r"...\2",
            message
        )
        
        # Remove stack trace details (line numbers, function names from internal code)
        message = re.sub(
            r"File \"[^\"]+\", line \d+, in \w+",
            "File [internal], line [N]",
            message
        )
        
        return message
    
    @classmethod
    def verify_file_exists(cls, path: Path | str) -> tuple[bool, str]:
        """
        Verify that a file exists and is readable.
        
        Args:
            path: Path to the file to verify.
            
        Returns:
            A tuple of (exists_and_readable, error_message).
        """
        path = Path(path)
        
        if not path.exists():
            return False, f"El archivo no existe: {path.name}"
        
        if not path.is_file():
            return False, f"La ruta no es un archivo: {path.name}"
        
        try:
            # Try to open the file to verify readability
            with open(path, "rb") as f:
                # Read first few bytes to verify
                f.read(10)
            return True, ""
        except PermissionError:
            return False, f"Sin permisos para leer: {path.name}"
        except OSError as e:
            return False, f"Error al leer archivo: {cls.sanitize_error_message(e)}"
    
    @classmethod
    def is_safe_for_logging(cls, text: str) -> bool:
        """
        Check if text is safe to include in logs (no sensitive data).
        
        Args:
            text: The text to check.
            
        Returns:
            True if safe, False if contains sensitive patterns.
        """
        for pattern in cls.SENSITIVE_PATTERNS:
            if pattern.search(text):
                return False
        return True
