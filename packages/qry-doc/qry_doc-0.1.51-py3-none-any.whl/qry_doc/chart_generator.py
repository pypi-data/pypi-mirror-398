"""
Chart generation utilities for qry-doc.

This module provides reliable chart generation using matplotlib,
independent of PandasAI's chart generation.
"""
from pathlib import Path
from typing import Optional, Union, Literal
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt


ChartType = Literal['bar', 'barh', 'line', 'pie', 'scatter', 'area']


class ChartGenerator:
    """
    Generates charts from DataFrames using matplotlib.
    
    Provides reliable chart generation for PDF reports.
    """
    
    # Default colors for charts
    COLORS = [
        '#2196F3',  # Blue
        '#4CAF50',  # Green
        '#FF9800',  # Orange
        '#E91E63',  # Pink
        '#9C27B0',  # Purple
        '#00BCD4',  # Cyan
        '#FF5722',  # Deep Orange
        '#607D8B',  # Blue Grey
    ]
    
    @classmethod
    def generate(
        cls,
        df: pd.DataFrame,
        output_path: Union[str, Path],
        chart_type: ChartType = 'bar',
        title: Optional[str] = None,
        x_column: Optional[str] = None,
        y_column: Optional[str] = None,
        figsize: tuple[int, int] = (10, 6),
        color: Optional[str] = None
    ) -> Path:
        """
        Generate a chart from a DataFrame.
        
        Args:
            df: DataFrame with data to plot.
            output_path: Path to save the chart image.
            chart_type: Type of chart ('bar', 'barh', 'line', 'pie', 'scatter', 'area').
            title: Chart title.
            x_column: Column to use for x-axis (or labels for pie).
            y_column: Column to use for y-axis (or values for pie).
            figsize: Figure size in inches (width, height).
            color: Color for the chart (hex or name).
            
        Returns:
            Path to the generated chart file.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Auto-detect columns if not specified
        if x_column is None or y_column is None:
            x_column, y_column = cls._auto_detect_columns(df)
        
        # Create figure
        fig, ax = plt.subplots(figsize=figsize)
        
        # Get data
        x_data = df[x_column] if x_column in df.columns else df.index
        y_data = df[y_column] if y_column in df.columns else df.iloc[:, 0]
        
        # Use default color if not specified
        chart_color = color or cls.COLORS[0]
        
        # Generate chart based on type
        if chart_type == 'bar':
            ax.bar(x_data, y_data, color=chart_color)
            ax.set_xlabel(x_column or 'Categoría')
            ax.set_ylabel(y_column or 'Valor')
            plt.xticks(rotation=45, ha='right')
            
        elif chart_type == 'barh':
            ax.barh(x_data, y_data, color=chart_color)
            ax.set_xlabel(y_column or 'Valor')
            ax.set_ylabel(x_column or 'Categoría')
            
        elif chart_type == 'line':
            ax.plot(x_data, y_data, color=chart_color, marker='o', linewidth=2)
            ax.set_xlabel(x_column or 'X')
            ax.set_ylabel(y_column or 'Y')
            plt.xticks(rotation=45, ha='right')
            ax.grid(True, alpha=0.3)
            
        elif chart_type == 'pie':
            colors = cls.COLORS[:len(x_data)]
            ax.pie(y_data, labels=x_data, autopct='%1.1f%%', colors=colors)
            ax.axis('equal')
            
        elif chart_type == 'scatter':
            ax.scatter(x_data, y_data, color=chart_color, alpha=0.7)
            ax.set_xlabel(x_column or 'X')
            ax.set_ylabel(y_column or 'Y')
            ax.grid(True, alpha=0.3)
            
        elif chart_type == 'area':
            ax.fill_between(range(len(y_data)), y_data, color=chart_color, alpha=0.5)
            ax.plot(range(len(y_data)), y_data, color=chart_color, linewidth=2)
            ax.set_xticks(range(len(x_data)))
            ax.set_xticklabels(x_data, rotation=45, ha='right')
            ax.set_xlabel(x_column or 'X')
            ax.set_ylabel(y_column or 'Y')
        
        # Set title
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold')
        
        # Adjust layout
        plt.tight_layout()
        
        # Save figure
        fig.savefig(output_path, dpi=150, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close(fig)
        
        return output_path
    
    @classmethod
    def _auto_detect_columns(cls, df: pd.DataFrame) -> tuple[str, str]:
        """
        Auto-detect the best columns for x and y axes.
        
        Returns:
            Tuple of (x_column, y_column).
        """
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        non_numeric_cols = df.select_dtypes(exclude=['number']).columns.tolist()
        
        # Prefer: categorical for x, numeric for y
        x_col = non_numeric_cols[0] if non_numeric_cols else df.columns[0]
        y_col = numeric_cols[0] if numeric_cols else df.columns[-1]
        
        return x_col, y_col
    
    @classmethod
    def generate_from_aggregation(
        cls,
        df: pd.DataFrame,
        output_path: Union[str, Path],
        group_by: str,
        value_column: str,
        agg_func: str = 'sum',
        chart_type: ChartType = 'bar',
        title: Optional[str] = None,
        top_n: Optional[int] = None
    ) -> Path:
        """
        Generate a chart from an aggregated DataFrame.
        
        Args:
            df: Source DataFrame.
            output_path: Path to save the chart.
            group_by: Column to group by.
            value_column: Column to aggregate.
            agg_func: Aggregation function ('sum', 'mean', 'count', 'max', 'min').
            chart_type: Type of chart.
            title: Chart title.
            top_n: Limit to top N results.
            
        Returns:
            Path to the generated chart file.
        """
        # Perform aggregation
        agg_df = df.groupby(group_by)[value_column].agg(agg_func).reset_index()
        agg_df.columns = [group_by, value_column]
        
        # Sort and limit
        agg_df = agg_df.sort_values(value_column, ascending=False)
        if top_n:
            agg_df = agg_df.head(top_n)
        
        # Generate chart
        return cls.generate(
            df=agg_df,
            output_path=output_path,
            chart_type=chart_type,
            title=title,
            x_column=group_by,
            y_column=value_column
        )
    
    @classmethod
    def auto_chart(
        cls,
        df: pd.DataFrame,
        output_path: Union[str, Path],
        title: Optional[str] = None
    ) -> Path:
        """
        Automatically generate the most appropriate chart for the data.
        
        Analyzes the DataFrame and chooses the best chart type.
        
        Args:
            df: DataFrame to visualize.
            output_path: Path to save the chart.
            title: Optional chart title.
            
        Returns:
            Path to the generated chart file.
        """
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        non_numeric_cols = df.select_dtypes(exclude=['number']).columns.tolist()
        
        n_rows = len(df)
        n_numeric = len(numeric_cols)
        n_categorical = len(non_numeric_cols)
        
        # Determine best chart type
        if n_rows <= 8 and n_categorical >= 1 and n_numeric >= 1:
            # Few categories -> pie chart
            chart_type = 'pie'
        elif n_categorical >= 1 and n_numeric >= 1:
            # Categories + values -> bar chart
            if n_rows > 10:
                chart_type = 'barh'  # Horizontal for many items
            else:
                chart_type = 'bar'
        elif n_numeric >= 2:
            # Multiple numeric -> line or scatter
            chart_type = 'line'
        else:
            # Default to bar
            chart_type = 'bar'
        
        return cls.generate(
            df=df,
            output_path=output_path,
            chart_type=chart_type,
            title=title
        )
