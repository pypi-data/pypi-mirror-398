"""
Core module for qry-doc library.

This module provides the QryDoc class, the main entry point (Facade)
for all library functionality.
"""
import os
from pathlib import Path
from typing import Any, Optional, Union

import pandas as pd

from qry_doc.ai_adapter import PandasAIAdapter
from qry_doc.ai_builder import AIBuilder
from qry_doc.chart_generator import ChartGenerator
from qry_doc.chart_manager import ChartManager
from qry_doc.cover_builder import CoverBuilder
from qry_doc.csv_exporter import CSVExporter
from qry_doc.data_source import DataSourceLoader
from qry_doc.exceptions import (
    QryDocError,
    QueryError,
    ExportError,
    ReportError,
    DataSourceError,
)
from qry_doc.report_generator import ReportGenerator
from qry_doc.report_template import ReportTemplate, DEFAULT_TEMPLATE
from qry_doc.template_builder import TemplateBuilder
from qry_doc.validators import OutputValidator


class QryDoc:
    """
    Main entry point for qry-doc library.
    
    QryDoc acts as a Facade, providing a simple interface to:
    - Ask natural language questions about data
    - Extract query results to CSV
    - Generate PDF reports with charts and tables
    
    Example:
        ```python
        from qry_doc import QryDoc
        from pandasai.llm import OpenAI
        
        llm = OpenAI(api_token="your-api-key")
        qry = QryDoc("data.csv", llm=llm)
        
        # Ask a question
        answer = qry.ask("What is the average sales?")
        
        # Export to CSV
        qry.extract_to_csv("Show top 10 customers", "top_customers.csv")
        
        # Generate PDF report
        qry.generate_report("Analyze sales trends", "report.pdf")
        ```
    """
    
    # Environment variable for API key fallback
    API_KEY_ENV_VAR = "OPENAI_API_KEY"
    
    def __init__(
        self,
        data_source: Union[str, Path, pd.DataFrame],
        llm: Any,
        api_key: Optional[str] = None
    ) -> None:
        """
        Initialize QryDoc with a data source and LLM provider.
        
        Args:
            data_source: Path to CSV file, pandas DataFrame, or SQL connection string.
            llm: LLM provider instance (OpenAI, Anthropic, LiteLLM, etc.).
            api_key: Optional API key (falls back to environment variable).
            
        Raises:
            DataSourceError: If the data source cannot be loaded.
        """
        # Load data
        self._df = DataSourceLoader.load(data_source)
        
        # Store LLM
        self._llm = llm
        
        # Handle API key (for reference, actual key is in llm)
        self._api_key = api_key or os.environ.get(self.API_KEY_ENV_VAR)
        
        # Initialize chart manager
        self._chart_manager = ChartManager()
        
        # Initialize AI adapter
        self._adapter = PandasAIAdapter(
            df=self._df,
            llm=self._llm,
            chart_save_path=self._chart_manager.path
        )
    
    def ask(self, query: str) -> str:
        """
        Ask a natural language question about the data.
        
        Args:
            query: Natural language question.
            
        Returns:
            A human-readable text response.
            
        Raises:
            QueryError: If the query cannot be processed.
            
        Example:
            ```python
            answer = qry.ask("What is the total revenue for 2023?")
            print(answer)  # "The total revenue for 2023 is $1,234,567"
            ```
        """
        try:
            return self._adapter.query_as_text(query)
        except QueryError:
            raise
        except Exception as e:
            sanitized = OutputValidator.sanitize_error_message(e)
            raise QueryError(
                user_message=f"No se pudo interpretar la consulta: {sanitized}. "
                            "Intente reformular la pregunta con más detalle.",
                internal_error=e
            )
    
    def extract_to_csv(
        self,
        query: str,
        output_path: Union[str, Path],
        include_index: bool = False
    ) -> str:
        """
        Execute a query and export results to CSV.
        
        Args:
            query: Natural language query requesting tabular data.
            output_path: Path for the output CSV file.
            include_index: Whether to include DataFrame index. Default False.
            
        Returns:
            Confirmation message with the output file path.
            
        Raises:
            QueryError: If the query cannot be processed.
            ExportError: If the result is not tabular or export fails.
            
        Example:
            ```python
            result = qry.extract_to_csv(
                "Show sales by region for Q4",
                "q4_sales.csv"
            )
            print(result)  # "Datos exportados exitosamente a q4_sales.csv"
            ```
        """
        try:
            # Get DataFrame result
            df = self._adapter.query_as_dataframe(query)
            
            # Validate result
            is_valid, error_msg = OutputValidator.validate_dataframe(df)
            if not is_valid:
                raise ExportError(user_message=error_msg)
            
            # Export to CSV
            return CSVExporter.export(
                df=df,
                path=output_path,
                include_index=include_index
            )
            
        except (QueryError, ExportError):
            raise
        except Exception as e:
            sanitized = OutputValidator.sanitize_error_message(e)
            raise ExportError(
                user_message=f"Error al exportar datos: {sanitized}",
                internal_error=e
            )
    
    def export_dataframe(
        self,
        output_path: Union[str, Path],
        include_index: bool = False
    ) -> str:
        """
        Export the entire underlying DataFrame to CSV.
        
        This is useful when you want to export all data without
        running a query through the LLM.
        
        Args:
            output_path: Path for the output CSV file.
            include_index: Whether to include DataFrame index. Default False.
            
        Returns:
            Confirmation message with the output file path.
            
        Example:
            ```python
            result = qry.export_dataframe("all_data.csv")
            ```
        """
        return CSVExporter.export(
            df=self._df,
            path=output_path,
            include_index=include_index
        )
    
    def filter_and_export(
        self,
        output_path: Union[str, Path],
        columns: Optional[list[str]] = None,
        filters: Optional[dict[str, Any]] = None,
        include_index: bool = False
    ) -> str:
        """
        Filter the DataFrame and export to CSV without using LLM.
        
        This provides a reliable way to export data when LLM queries
        are not returning consistent results.
        
        Args:
            output_path: Path for the output CSV file.
            columns: List of columns to include. None = all columns.
            filters: Dict of column:value pairs to filter by.
            include_index: Whether to include DataFrame index.
            
        Returns:
            Confirmation message with the output file path.
            
        Example:
            ```python
            # Export specific columns
            qry.filter_and_export(
                "ventas_norte.csv",
                columns=["producto", "cantidad", "precio"],
                filters={"region": "Norte"}
            )
            ```
        """
        df = self._df.copy()
        
        # Apply filters
        if filters:
            for col, value in filters.items():
                if col in df.columns:
                    df = df[df[col] == value]
        
        # Select columns
        if columns:
            valid_cols = [c for c in columns if c in df.columns]
            if valid_cols:
                df = df[valid_cols]
        
        return CSVExporter.export(
            df=df,
            path=output_path,
            include_index=include_index
        )
    
    def generate_report(
        self,
        query: str,
        output_path: Union[str, Path],
        title: str = "Reporte Automático",
        template: Optional[ReportTemplate] = None,
        include_chart: bool = True,
        include_table: bool = True,
        chart_type: str = 'auto',
        group_by: Optional[str] = None,
        value_column: Optional[str] = None
    ) -> str:
        """
        Generate a PDF report based on a query.
        
        The report includes:
        - Title and executive summary
        - Relevant charts/visualizations (if applicable)
        - Data tables (if applicable)
        
        Args:
            query: Natural language query describing the analysis.
            output_path: Path for the output PDF file.
            title: Report title. Default "Reporte Automático".
            template: Optional ReportTemplate for custom styling.
            include_chart: Whether to include a chart. Default True.
            include_table: Whether to include a data table. Default True.
            chart_type: Type of chart ('auto', 'bar', 'barh', 'line', 'pie').
            group_by: Column to group data by for the chart.
            value_column: Column with values to plot.
            
        Returns:
            Confirmation message with the output file path.
            
        Raises:
            QueryError: If the query cannot be processed.
            ReportError: If report generation fails.
            
        Example:
            ```python
            result = qry.generate_report(
                "Analiza las ventas por categoría",
                "reporte.pdf",
                title="Análisis de Ventas",
                include_chart=True,
                chart_type='bar',
                group_by='categoria',
                value_column='total'
            )
            ```
        """
        try:
            # Clear previous charts
            self._chart_manager.clear_charts()
            
            # Step 1: Get textual summary
            summary = self._adapter.query_as_text(
                f"Analyze the data regarding: {query}. Provide a comprehensive summary."
            )
            
            # Step 2: Generate chart using our reliable chart generator
            chart_path = None
            if include_chart:
                try:
                    # Create temp path for chart
                    chart_temp_path = self._chart_manager.path / "report_chart.png"
                    
                    # Auto-detect columns if not specified
                    if group_by is None:
                        # Find best categorical column
                        non_numeric = self._df.select_dtypes(exclude=['number']).columns
                        group_by = non_numeric[0] if len(non_numeric) > 0 else self._df.columns[0]
                    
                    if value_column is None:
                        # Find best numeric column
                        numeric = self._df.select_dtypes(include=['number']).columns
                        value_column = numeric[0] if len(numeric) > 0 else self._df.columns[-1]
                    
                    # Generate aggregated chart
                    if group_by in self._df.columns and value_column in self._df.columns:
                        agg_df = self._df.groupby(group_by)[value_column].sum().reset_index()
                        agg_df = agg_df.sort_values(value_column, ascending=False).head(10)
                        
                        # Determine chart type
                        if chart_type == 'auto':
                            n_categories = len(agg_df)
                            if n_categories <= 6:
                                actual_chart_type = 'pie'
                            elif n_categories <= 10:
                                actual_chart_type = 'bar'
                            else:
                                actual_chart_type = 'barh'
                        else:
                            actual_chart_type = chart_type
                        
                        chart_path = ChartGenerator.generate(
                            df=agg_df,
                            output_path=chart_temp_path,
                            chart_type=actual_chart_type,
                            title=f"{value_column} por {group_by}",
                            x_column=group_by,
                            y_column=value_column
                        )
                except Exception as e:
                    # Chart generation failed, continue without chart
                    print(f"Advertencia: No se pudo generar gráfica: {e}")
                    chart_path = None
            
            # Step 3: Try to get tabular data
            table_data = None
            if include_table:
                try:
                    # Use aggregated data if we have group_by
                    if group_by and value_column:
                        table_data = self._df.groupby(group_by)[value_column].agg(['sum', 'mean', 'count']).reset_index()
                        table_data.columns = [group_by, 'Total', 'Promedio', 'Cantidad']
                    else:
                        table_data = self._df.head(20)  # First 20 rows
                except Exception:
                    table_data = None
            
            # Step 4: Generate PDF
            generator = ReportGenerator(
                output_path=output_path,
                template=template or DEFAULT_TEMPLATE
            )
            
            generator.build(
                title=title,
                summary=summary,
                chart_path=chart_path,
                dataframe=table_data
            )
            
            return f"Reporte generado exitosamente en {output_path}"
            
        except (QueryError, ReportError):
            raise
        except Exception as e:
            sanitized = OutputValidator.sanitize_error_message(e)
            raise ReportError(
                user_message=f"Error al generar el reporte: {sanitized}",
                internal_error=e
            )
        finally:
            # Clean up charts
            self._chart_manager.clear_charts()
    
    def generate_chart(
        self,
        output_path: Union[str, Path],
        chart_type: str = 'auto',
        group_by: Optional[str] = None,
        value_column: Optional[str] = None,
        title: Optional[str] = None,
        top_n: int = 10
    ) -> Path:
        """
        Generate a chart from the data.
        
        Args:
            output_path: Path to save the chart image.
            chart_type: Type of chart ('auto', 'bar', 'barh', 'line', 'pie', 'scatter').
            group_by: Column to group data by.
            value_column: Column with values to plot.
            title: Chart title.
            top_n: Limit to top N results.
            
        Returns:
            Path to the generated chart file.
            
        Example:
            ```python
            # Auto chart
            qry.generate_chart("chart.png")
            
            # Specific chart
            qry.generate_chart(
                "ventas_categoria.png",
                chart_type='bar',
                group_by='categoria',
                value_column='total',
                title='Ventas por Categoría'
            )
            ```
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Auto-detect columns if not specified
        if group_by is None:
            non_numeric = self._df.select_dtypes(exclude=['number']).columns
            group_by = non_numeric[0] if len(non_numeric) > 0 else self._df.columns[0]
        
        if value_column is None:
            numeric = self._df.select_dtypes(include=['number']).columns
            value_column = numeric[0] if len(numeric) > 0 else self._df.columns[-1]
        
        # Aggregate data
        if group_by in self._df.columns and value_column in self._df.columns:
            agg_df = self._df.groupby(group_by)[value_column].sum().reset_index()
            agg_df = agg_df.sort_values(value_column, ascending=False).head(top_n)
        else:
            agg_df = self._df.head(top_n)
        
        # Determine chart type
        if chart_type == 'auto':
            n_categories = len(agg_df)
            if n_categories <= 6:
                actual_chart_type = 'pie'
            elif n_categories <= 10:
                actual_chart_type = 'bar'
            else:
                actual_chart_type = 'barh'
        else:
            actual_chart_type = chart_type
        
        # Generate chart
        return ChartGenerator.generate(
            df=agg_df,
            output_path=output_path,
            chart_type=actual_chart_type,
            title=title or f"{value_column} por {group_by}",
            x_column=group_by,
            y_column=value_column
        )
    
    def generate_report_with_builder(
        self,
        output_path: Union[str, Path],
        cover: Optional[CoverBuilder] = None,
        template: Optional[TemplateBuilder] = None,
        title: str = "Reporte Automático",
        summary: Optional[str] = None,
        include_table: bool = True,
    ) -> str:
        """
        Generate a PDF report using CoverBuilder and TemplateBuilder.
        
        This method provides a more flexible way to generate reports
        using the builder pattern for covers and templates.
        
        Args:
            output_path: Path for the output PDF file.
            cover: Optional CoverBuilder for dynamic cover.
            template: Optional TemplateBuilder for custom styling.
            title: Report title.
            summary: Optional summary text. If not provided, generates one.
            include_table: Whether to include a data table.
            
        Returns:
            Confirmation message with the output file path.
            
        Raises:
            ReportError: If report generation fails.
            
        Example:
            ```python
            cover = qry.create_cover()
            cover.set_title("Sales Report")
            cover.set_author("Data Team")
            
            template = qry.create_template()
            template.with_colors("#003366")
            
            qry.generate_report_with_builder(
                "report.pdf",
                cover=cover,
                template=template
            )
            ```
        """
        from qry_doc.chart_config import ChartConfig
        
        try:
            # Build template if provided
            report_template = DEFAULT_TEMPLATE
            charts: list[ChartConfig] = []
            
            if template is not None:
                report_template = template.build()
                charts = template.charts
            
            # Apply cover if provided
            if cover is not None:
                cover_config = cover.build()
                if cover_config.background_image:
                    report_template = ReportTemplate(
                        primary_color=report_template.primary_color,
                        secondary_color=report_template.secondary_color,
                        title_font=report_template.title_font,
                        body_font=report_template.body_font,
                        margin_top=report_template.margin_top,
                        margin_bottom=report_template.margin_bottom,
                        margin_left=report_template.margin_left,
                        margin_right=report_template.margin_right,
                        header_logo_path=report_template.header_logo_path,
                        header_height=report_template.header_height,
                        footer_logo_path=report_template.footer_logo_path,
                        footer_logo_position=report_template.footer_logo_position,
                        footer_height=report_template.footer_height,
                        cover_image_path=cover_config.background_image,
                        sections=report_template.sections,
                    )
            
            # Generate summary if not provided
            if summary is None:
                summary = self._adapter.query_as_text(
                    "Provide a comprehensive summary of the data."
                )
            
            # Get table data
            table_data = None
            if include_table:
                table_data = self._df.head(20)
            
            # Create generator
            generator = ReportGenerator(
                output_path=output_path,
                template=report_template
            )
            
            # Build with charts if available
            if charts:
                generator.build_with_charts(
                    title=title,
                    summary=summary,
                    charts=charts,
                    dataframe=table_data if table_data is not None else self._df,
                )
            else:
                generator.build(
                    title=title,
                    summary=summary,
                    dataframe=table_data
                )
            
            return f"Reporte generado exitosamente en {output_path}"
            
        except Exception as e:
            sanitized = OutputValidator.sanitize_error_message(e)
            raise ReportError(
                user_message=f"Error al generar el reporte: {sanitized}",
                internal_error=e
            )
    
    @property
    def dataframe(self) -> pd.DataFrame:
        """Get the underlying DataFrame."""
        return self._df
    
    @property
    def columns(self) -> list[str]:
        """Get the column names of the data."""
        return list(self._df.columns)
    
    @property
    def shape(self) -> tuple[int, int]:
        """Get the shape of the data (rows, columns)."""
        return self._df.shape
    
    @property
    def ai_builder(self) -> AIBuilder:
        """
        Get an AIBuilder instance configured with the same LLM.
        
        The AIBuilder helps with intelligent data selection and
        report preparation using LangChain.
        
        Returns:
            AIBuilder instance configured with the DataFrame and LLM.
            
        Example:
            ```python
            ai = qry.ai_builder
            suggestions = ai.suggest_charts("sales analysis")
            ```
        """
        return AIBuilder(df=self._df, llm=self._llm)
    
    def create_cover(self) -> CoverBuilder:
        """
        Create a new CoverBuilder for building dynamic covers.
        
        Returns:
            New CoverBuilder instance.
            
        Example:
            ```python
            cover = qry.create_cover()
            cover.set_title("Sales Report 2024")
            cover.set_subtitle("Q4 Analysis")
            cover.set_author("Data Team")
            ```
        """
        return CoverBuilder()
    
    def create_template(self) -> TemplateBuilder:
        """
        Create a new TemplateBuilder for building custom templates.
        
        Returns:
            New TemplateBuilder instance.
            
        Example:
            ```python
            template = qry.create_template()
            template.with_colors("#003366", "#666666")
            template.with_fonts("Helvetica-Bold", "Helvetica")
            ```
        """
        return TemplateBuilder()
    
    def __enter__(self) -> "QryDoc":
        """Enter context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager, cleaning up resources."""
        self._chart_manager.cleanup()
    
    def __del__(self) -> None:
        """Destructor - ensure cleanup."""
        if hasattr(self, '_chart_manager'):
            self._chart_manager.cleanup()
