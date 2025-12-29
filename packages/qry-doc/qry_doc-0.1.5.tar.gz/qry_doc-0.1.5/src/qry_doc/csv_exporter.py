"""
CSV export utilities for qry-doc.

This module provides functionality to export pandas DataFrames to CSV files
with sensible defaults for Excel compatibility.
"""
from pathlib import Path
from typing import Any, Union

import pandas as pd

from qry_doc.exceptions import ExportError
from qry_doc.validators import OutputValidator


class CSVExporter:
    """
    Exports pandas DataFrames to CSV files.
    
    Features:
    - UTF-8-sig encoding by default (Excel compatible)
    - Index exclusion by default
    - DataFrame validation before export
    """
    
    # Default encoding with BOM for Excel compatibility
    DEFAULT_ENCODING = "utf-8-sig"
    
    @classmethod
    def export(
        cls,
        df: pd.DataFrame,
        path: Union[str, Path],
        include_index: bool = False,
        encoding: str = DEFAULT_ENCODING
    ) -> str:
        """
        Export a DataFrame to a CSV file.
        
        Args:
            df: The DataFrame to export.
            path: Output file path.
            include_index: Whether to include the DataFrame index. Default False.
            encoding: File encoding. Default 'utf-8-sig' for Excel compatibility.
            
        Returns:
            A confirmation message with the output file path.
            
        Raises:
            ExportError: If validation fails or export encounters an error.
        """
        # Validate the DataFrame
        is_valid, error_msg = cls.validate_dataframe(df)
        if not is_valid:
            raise ExportError(user_message=error_msg)
        
        # Convert to Path
        output_path = Path(path)
        
        # Ensure parent directory exists
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            raise ExportError(
                user_message=f"Sin permisos para crear el directorio: {output_path.parent}"
            )
        
        # Export to CSV
        try:
            df.to_csv(
                output_path,
                index=include_index,
                encoding=encoding
            )
        except PermissionError:
            raise ExportError(
                user_message=f"Sin permisos para escribir el archivo: {output_path.name}"
            )
        except OSError as e:
            raise ExportError(
                user_message=f"Error al escribir el archivo: {output_path.name}",
                internal_error=e
            )
        
        return f"Datos exportados exitosamente a {output_path}"
    
    @classmethod
    def validate_dataframe(cls, data: Any) -> tuple[bool, str]:
        """
        Validate that data is a valid DataFrame suitable for CSV export.
        
        Args:
            data: The data to validate.
            
        Returns:
            A tuple of (is_valid, error_message).
        """
        return OutputValidator.validate_dataframe(data)
    
    @classmethod
    def get_encoding_bom(cls, encoding: str) -> bytes:
        """
        Get the BOM (Byte Order Mark) for the given encoding.
        
        Args:
            encoding: The encoding name.
            
        Returns:
            The BOM bytes, or empty bytes if no BOM.
        """
        if encoding.lower() in ("utf-8-sig", "utf_8_sig"):
            return b"\xef\xbb\xbf"
        elif encoding.lower() in ("utf-16", "utf_16"):
            return b"\xff\xfe"
        return b""
