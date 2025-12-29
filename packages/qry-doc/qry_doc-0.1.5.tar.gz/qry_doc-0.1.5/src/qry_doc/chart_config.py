"""
Chart configuration for multi-chart report support.

This module provides ChartConfig dataclass for configuring individual
charts within a report, supporting multiple chart types and styling options.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal, Optional, Tuple

from qry_doc.text_element import is_valid_hex_color
from qry_doc.exceptions import ValidationError


# Supported chart types
ChartType = Literal['bar', 'barh', 'line', 'pie', 'scatter', 'area']

# Valid chart type values for validation
VALID_CHART_TYPES = {'bar', 'barh', 'line', 'pie', 'scatter', 'area'}

# Default figure size in inches (width, height)
DEFAULT_FIGSIZE: Tuple[int, int] = (10, 6)

# Maximum charts per report
MAX_CHARTS_PER_REPORT = 10


class ChartTypeEnum(Enum):
    """Enumeration of supported chart types."""
    BAR = "bar"
    BARH = "barh"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    AREA = "area"


@dataclass
class ChartConfig:
    """
    Configuration for a single chart in a report.
    
    Defines the chart type, data source, and styling options for
    rendering a chart within a PDF report.
    
    Attributes:
        chart_type: Type of chart to render ('bar', 'barh', 'line', 'pie', 'scatter', 'area').
        title: Title displayed above the chart.
        data_query: Optional natural language query to generate chart data.
        group_by: Optional column name for grouping data.
        value_column: Optional column name for values to aggregate.
        color: Optional hex color for chart elements.
        figsize: Figure size as (width, height) in inches.
    
    Example:
        ```python
        chart = ChartConfig(
            chart_type='bar',
            title='Sales by Region',
            group_by='region',
            value_column='sales',
            color='#003366'
        )
        ```
    """
    chart_type: ChartType
    title: str
    data_query: Optional[str] = None
    group_by: Optional[str] = None
    value_column: Optional[str] = None
    color: Optional[str] = None
    figsize: Tuple[int, int] = field(default_factory=lambda: DEFAULT_FIGSIZE)
    
    def __post_init__(self) -> None:
        """Normalize color to uppercase if provided."""
        if self.color is not None:
            self.color = self.color.upper()
    
    def validate(self) -> Tuple[bool, Optional[str]]:
        """
        Validate the chart configuration.
        
        Checks that:
        - chart_type is one of the supported types
        - title is not empty
        - color (if provided) is a valid hex format
        - figsize has positive dimensions
        
        Returns:
            Tuple of (is_valid, error_message).
            If valid, returns (True, None).
            If invalid, returns (False, error_description).
        """
        # Validate chart_type
        if self.chart_type not in VALID_CHART_TYPES:
            return (
                False,
                f"Invalid chart_type '{self.chart_type}'. "
                f"Must be one of: {', '.join(sorted(VALID_CHART_TYPES))}"
            )
        
        # Validate title
        if not self.title or not self.title.strip():
            return (False, "Chart title cannot be empty")
        
        # Validate color if provided
        if self.color is not None and not is_valid_hex_color(self.color):
            return (
                False,
                f"Invalid color format '{self.color}'. Use hex format like '#FF0000'"
            )
        
        # Validate figsize
        if len(self.figsize) != 2:
            return (False, "figsize must be a tuple of (width, height)")
        
        width, height = self.figsize
        if width <= 0 or height <= 0:
            return (False, f"figsize dimensions must be positive, got ({width}, {height})")
        
        return (True, None)
    
    def validate_or_raise(self) -> None:
        """
        Validate the chart configuration, raising ValidationError if invalid.
        
        Raises:
            ValidationError: If the configuration is invalid.
        """
        is_valid, error_msg = self.validate()
        if not is_valid:
            raise ValidationError(
                user_message=error_msg or "Invalid chart configuration",
                internal_error=None
            )
    
    @classmethod
    def create(
        cls,
        chart_type: ChartType,
        title: str,
        data_query: Optional[str] = None,
        group_by: Optional[str] = None,
        value_column: Optional[str] = None,
        color: Optional[str] = None,
        figsize: Optional[Tuple[int, int]] = None,
    ) -> "ChartConfig":
        """
        Create a validated ChartConfig instance.
        
        Factory method that creates and validates a ChartConfig,
        raising ValidationError if the configuration is invalid.
        
        Args:
            chart_type: Type of chart to render.
            title: Title displayed above the chart.
            data_query: Optional natural language query.
            group_by: Optional column name for grouping.
            value_column: Optional column name for values.
            color: Optional hex color for chart elements.
            figsize: Optional figure size as (width, height).
            
        Returns:
            Validated ChartConfig instance.
            
        Raises:
            ValidationError: If the configuration is invalid.
        """
        config = cls(
            chart_type=chart_type,
            title=title,
            data_query=data_query,
            group_by=group_by,
            value_column=value_column,
            color=color,
            figsize=figsize or DEFAULT_FIGSIZE,
        )
        config.validate_or_raise()
        return config


def validate_chart_list(charts: list[ChartConfig]) -> Tuple[bool, Optional[str]]:
    """
    Validate a list of chart configurations.
    
    Checks that:
    - The list does not exceed MAX_CHARTS_PER_REPORT
    - Each chart configuration is valid
    
    Args:
        charts: List of ChartConfig objects to validate.
        
    Returns:
        Tuple of (is_valid, error_message).
    """
    if len(charts) > MAX_CHARTS_PER_REPORT:
        return (
            False,
            f"Maximum {MAX_CHARTS_PER_REPORT} charts per report, got {len(charts)}"
        )
    
    for i, chart in enumerate(charts):
        is_valid, error_msg = chart.validate()
        if not is_valid:
            return (False, f"Chart {i + 1}: {error_msg}")
    
    return (True, None)
