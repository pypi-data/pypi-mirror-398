"""
PandasAI adapter for qry-doc.

This module provides the PandasAIAdapter class that wraps PandasAI
functionality and adapts it to the qry-doc interface.
"""
import re
from pathlib import Path
from typing import Any, Optional, Protocol, Union

import pandas as pd
from pandasai import SmartDataframe

from qry_doc.exceptions import QueryError
from qry_doc.validators import OutputValidator


class LLMProvider(Protocol):
    """
    Protocol for LLM providers.
    
    Any LLM that implements this interface can be used with qry-doc.
    Compatible with OpenAI, Anthropic, LiteLLM, and local models.
    """
    
    def __call__(self, prompt: str) -> str:
        """Generate a response for the given prompt."""
        ...


class PandasAIAdapter:
    """
    Adapter for PandasAI that provides a consistent interface for qry-doc.
    
    Features:
    - Query execution with type-specific returns
    - Prompt engineering for DataFrame/text responses
    - Chart path configuration
    - Error handling and sanitization
    """
    
    # Prompt templates for DataFrame output
    DATAFRAME_PROMPTS = [
        # Primary: explicit DataFrame request
        (
            "Execute this query and return ONLY a pandas DataFrame as the result. "
            "Do not return text explanations. Query: {query}"
        ),
        # Fallback 1: filter/select style
        (
            "Filter and select data to answer: {query}. "
            "Return the result as a DataFrame with appropriate columns."
        ),
        # Fallback 2: aggregation style  
        (
            "Create a summary table for: {query}. "
            "Return as DataFrame with descriptive column names."
        ),
    ]
    
    TEXT_SUFFIX = " Provide a clear, conversational answer explaining the result."
    
    def __init__(
        self,
        df: pd.DataFrame,
        llm: Any,
        chart_save_path: Optional[Path] = None
    ) -> None:
        """
        Initialize the PandasAI adapter.
        
        Args:
            df: The DataFrame to query.
            llm: The LLM provider (OpenAI, Anthropic, etc.).
            chart_save_path: Optional path for saving generated charts.
        """
        self._df = df
        self._llm = llm
        self._chart_save_path = chart_save_path
        
        # Configure PandasAI
        config = {
            "llm": llm,
            "enable_cache": False,  # Disable cache for fresh results
            "open_charts": False,   # Don't open chart windows
        }
        
        if chart_save_path:
            config["save_charts"] = True
            config["save_charts_path"] = str(chart_save_path)
        
        self._sdf = SmartDataframe(df, config=config)
    
    def query(self, question: str) -> Any:
        """
        Execute a query and return the raw result.
        
        Args:
            question: Natural language question about the data.
            
        Returns:
            The raw result from PandasAI (could be DataFrame, string, number, etc.).
            
        Raises:
            QueryError: If the query fails.
        """
        try:
            result = self._sdf.chat(question)
            return result
        except Exception as e:
            sanitized = OutputValidator.sanitize_error_message(e)
            raise QueryError(
                user_message=f"Error al procesar la consulta: {sanitized}",
                internal_error=e
            )
    
    def _convert_to_dataframe(self, result: Any) -> Optional[pd.DataFrame]:
        """
        Try to convert any result to a DataFrame.
        
        Args:
            result: The result from PandasAI query.
            
        Returns:
            DataFrame if conversion successful, None otherwise.
        """
        # Already a DataFrame
        if isinstance(result, pd.DataFrame):
            return result if not result.empty else None
        
        # List of dicts -> DataFrame
        if isinstance(result, list):
            if len(result) > 0:
                if isinstance(result[0], dict):
                    try:
                        return pd.DataFrame(result)
                    except Exception:
                        pass
                # List of lists or values
                try:
                    return pd.DataFrame(result)
                except Exception:
                    pass
        
        # Single dict -> DataFrame (single row or columns)
        if isinstance(result, dict):
            try:
                # Try as columns first
                df = pd.DataFrame(result)
                if not df.empty:
                    return df
            except Exception:
                pass
            try:
                # Try as single row
                return pd.DataFrame([result])
            except Exception:
                pass
        
        # Numeric or string scalar -> single cell DataFrame
        if isinstance(result, (int, float)):
            return pd.DataFrame({"valor": [result]})
        
        if isinstance(result, str):
            # Try to parse table from text response
            df = self._parse_table_from_text(result)
            if df is not None:
                return df
        
        return None
    
    def _parse_table_from_text(self, text: str) -> Optional[pd.DataFrame]:
        """
        Try to extract tabular data from a text response.
        
        Handles common formats like markdown tables or CSV-like text.
        """
        if not text or len(text) < 5:
            return None
        
        lines = text.strip().split('\n')
        
        # Try markdown table format (| col1 | col2 |)
        table_lines = [l for l in lines if '|' in l and not l.strip().startswith('|-')]
        if len(table_lines) >= 2:
            try:
                # Parse markdown table
                rows = []
                for line in table_lines:
                    cells = [c.strip() for c in line.split('|') if c.strip()]
                    if cells:
                        rows.append(cells)
                if len(rows) >= 2:
                    df = pd.DataFrame(rows[1:], columns=rows[0])
                    return df
            except Exception:
                pass
        
        # Try CSV-like format (comma or tab separated)
        if len(lines) >= 2:
            for sep in [',', '\t', ';']:
                try:
                    if sep in lines[0]:
                        from io import StringIO
                        df = pd.read_csv(StringIO(text), sep=sep)
                        if not df.empty and len(df.columns) > 1:
                            return df
                except Exception:
                    pass
        
        return None
    
    def query_as_dataframe(self, question: str, max_retries: int = 3) -> pd.DataFrame:
        """
        Execute a query and ensure the result is a DataFrame.
        
        Uses multiple prompt strategies and conversion attempts.
        
        Args:
            question: Natural language question about the data.
            max_retries: Maximum number of prompt variations to try.
            
        Returns:
            A pandas DataFrame with the query results.
            
        Raises:
            QueryError: If the query fails or doesn't return a DataFrame.
        """
        last_error = None
        
        for i, prompt_template in enumerate(self.DATAFRAME_PROMPTS[:max_retries]):
            try:
                enhanced_question = prompt_template.format(query=question)
                result = self._sdf.chat(enhanced_question)
                
                # Try to convert result to DataFrame
                df = self._convert_to_dataframe(result)
                if df is not None and not df.empty:
                    return df
                    
            except Exception as e:
                last_error = e
                continue
        
        # Final attempt: query the raw DataFrame directly if question is simple
        try:
            # Try a direct filter on the DataFrame
            result = self._sdf.chat(
                f"Return a filtered DataFrame based on: {question}. "
                "If no filter applies, return the full DataFrame."
            )
            df = self._convert_to_dataframe(result)
            if df is not None and not df.empty:
                return df
        except Exception:
            pass
        
        # If all attempts failed, raise error
        error_msg = (
            "No se pudo obtener datos tabulares. Sugerencias:\n"
            "- Use frases como 'Muestra una tabla con...'\n"
            "- Especifique las columnas: 'producto, cantidad, precio'\n"
            "- Para agregaciones: 'Agrupa por X mostrando Y'"
        )
        raise QueryError(
            user_message=error_msg,
            internal_error=last_error
        )
    
    def query_as_text(self, question: str) -> str:
        """
        Execute a query and ensure the result is a text response.
        
        Uses prompt engineering to encourage conversational output.
        
        Args:
            question: Natural language question about the data.
            
        Returns:
            A string with the conversational response.
            
        Raises:
            QueryError: If the query fails.
        """
        # Enhance prompt to request conversational output
        enhanced_question = question + self.TEXT_SUFFIX
        
        try:
            result = self._sdf.chat(enhanced_question)
            
            # Convert result to string
            if isinstance(result, str):
                return result
            
            if isinstance(result, pd.DataFrame):
                # Summarize DataFrame as text
                if result.empty:
                    return "No se encontraron datos que coincidan con la consulta."
                
                # Create a simple text summary
                n_rows, n_cols = result.shape
                summary = f"Se encontraron {n_rows} registros con {n_cols} columnas.\n\n"
                
                # Add first few rows as text
                if n_rows <= 5:
                    summary += result.to_string(index=False)
                else:
                    summary += f"Primeros 5 registros:\n{result.head().to_string(index=False)}"
                
                return summary
            
            # Convert other types to string
            return str(result)
            
        except QueryError:
            raise
        except Exception as e:
            sanitized = OutputValidator.sanitize_error_message(e)
            raise QueryError(
                user_message=f"Error al procesar la consulta: {sanitized}",
                internal_error=e
            )
    
    def generate_chart(self, question: str) -> Optional[Path]:
        """
        Execute a query that generates a chart.
        
        Args:
            question: Natural language question requesting a visualization.
            
        Returns:
            Path to the generated chart file, or None if no chart was created.
            
        Raises:
            QueryError: If the query fails.
        """
        if not self._chart_save_path:
            raise QueryError(
                user_message="No se configuró una ruta para guardar gráficos."
            )
        
        # Enhance prompt to request chart
        chart_question = f"Create a chart or plot showing: {question}"
        
        try:
            self._sdf.chat(chart_question)
            
            # Look for generated chart
            chart_path = Path(self._chart_save_path)
            if chart_path.is_dir():
                # Find most recent chart file
                charts = list(chart_path.glob("*.png")) + list(chart_path.glob("*.jpg"))
                if charts:
                    charts.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                    return charts[0]
            
            return None
            
        except QueryError:
            raise
        except Exception as e:
            sanitized = OutputValidator.sanitize_error_message(e)
            raise QueryError(
                user_message=f"Error al generar el gráfico: {sanitized}",
                internal_error=e
            )
    
    @property
    def dataframe(self) -> pd.DataFrame:
        """Get the underlying DataFrame."""
        return self._df
    
    @property
    def columns(self) -> list[str]:
        """Get the column names of the DataFrame."""
        return list(self._df.columns)
    
    @property
    def shape(self) -> tuple[int, int]:
        """Get the shape of the DataFrame (rows, columns)."""
        return self._df.shape
