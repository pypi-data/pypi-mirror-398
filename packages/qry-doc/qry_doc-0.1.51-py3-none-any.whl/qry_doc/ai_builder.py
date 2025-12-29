"""
AI Builder for intelligent report data preparation.

This module provides the AIBuilder class, an intelligent agent that helps
users select and prepare data for reports using LangChain for orchestration.
"""
from dataclasses import dataclass, field
from typing import Any, Optional, Union

import pandas as pd

from qry_doc.chart_config import ChartConfig, VALID_CHART_TYPES
from qry_doc.exceptions import ValidationError, QueryError

import logging

logger = logging.getLogger(__name__)


@dataclass
class DataSummary:
    """Structured summary of DataFrame data."""
    columns: list[str]
    dtypes: dict[str, str]
    shape: tuple[int, int]
    sample: dict[str, Any]
    numeric_columns: list[str]
    categorical_columns: list[str]
    null_counts: dict[str, int]


@dataclass
class ChartSuggestion:
    """A suggested chart configuration with reasoning."""
    config: ChartConfig
    reasoning: str
    confidence: float = 0.8


class AIBuilder:
    """
    Intelligent agent for report data preparation.
    
    AIBuilder uses LangChain to orchestrate interactions with the LLM,
    helping users select appropriate data and visualizations for reports.
    
    Features:
    - Analyze data structure and suggest appropriate charts
    - Prepare structured data for reports based on natural language
    - Validate queries before execution
    - Maintain conversation context for iterative refinement
    
    Example:
        ```python
        from qry_doc import QryDoc
        from pandasai.llm import OpenAI
        
        llm = OpenAI(api_token="your-key")
        qry = QryDoc("data.csv", llm=llm)
        
        # Get AI builder
        ai = qry.ai_builder
        
        # Get data summary
        summary = ai.get_data_summary()
        
        # Get chart suggestions
        charts = ai.suggest_charts("I want to analyze sales trends")
        
        # Prepare report data
        data = ai.prepare_report_data("Create a quarterly sales report")
        ```
    """
    
    # Maximum conversation context messages
    MAX_CONTEXT_MESSAGES = 20
    
    def __init__(
        self,
        df: pd.DataFrame,
        llm: Any,
        verbose: bool = False
    ) -> None:
        """
        Initialize AIBuilder with data and LLM.
        
        Args:
            df: DataFrame to analyze and prepare data from.
            llm: LLM provider instance (same as used by QryDoc).
            verbose: Whether to log detailed information.
        """
        self._df = df
        self._llm = llm
        self._verbose = verbose
        self._context: list[dict[str, str]] = []
        self._chain = None
        self._langchain_available = self._check_langchain()
    
    def _check_langchain(self) -> bool:
        """Check if LangChain is available."""
        try:
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import StrOutputParser
            return True
        except ImportError:
            logger.warning(
                "LangChain not installed. Install with: pip install qry-doc[langchain]"
            )
            return False
    
    def _build_chain(self) -> Any:
        """
        Build the LangChain chain for data analysis.
        
        Returns:
            LangChain chain or None if LangChain not available.
        """
        if not self._langchain_available:
            return None
        
        try:
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import StrOutputParser
            
            # Create prompt template for data analysis
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a data analysis assistant helping prepare data for reports.
You have access to a DataFrame with the following structure:
{data_summary}

Your task is to help users:
1. Understand their data
2. Suggest appropriate visualizations
3. Prepare data for reports

Always respond in a structured, helpful manner."""),
                ("human", "{query}")
            ])
            
            # Build chain with LLM
            # Note: The LLM from PandasAI may need adaptation
            chain = prompt | self._llm | StrOutputParser()
            return chain
            
        except Exception as e:
            logger.warning(f"Failed to build LangChain chain: {e}")
            return None
    
    def get_data_summary(self) -> DataSummary:
        """
        Get a structured summary of the data.
        
        Returns:
            DataSummary object with column info, types, and sample data.
        """
        # Get column types
        numeric_cols = self._df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = self._df.select_dtypes(exclude=['number']).columns.tolist()
        
        # Get null counts
        null_counts = self._df.isnull().sum().to_dict()
        
        return DataSummary(
            columns=list(self._df.columns),
            dtypes={col: str(dtype) for col, dtype in self._df.dtypes.items()},
            shape=self._df.shape,
            sample=self._df.head(3).to_dict(),
            numeric_columns=numeric_cols,
            categorical_columns=categorical_cols,
            null_counts=null_counts,
        )
    
    def suggest_charts(
        self,
        context: Optional[str] = None
    ) -> list[ChartSuggestion]:
        """
        Suggest appropriate charts based on data analysis.
        
        Analyzes the DataFrame structure and optionally considers
        user context to recommend suitable visualizations.
        
        Args:
            context: Optional description of what the user wants to analyze.
            
        Returns:
            List of ChartSuggestion objects with configs and reasoning.
        """
        suggestions: list[ChartSuggestion] = []
        summary = self.get_data_summary()
        
        # Rule-based suggestions based on data structure
        numeric_cols = summary.numeric_columns
        categorical_cols = summary.categorical_columns
        
        # Suggestion 1: Bar chart for categorical + numeric
        if categorical_cols and numeric_cols:
            cat_col = categorical_cols[0]
            num_col = numeric_cols[0]
            n_categories = self._df[cat_col].nunique()
            
            # Choose chart type based on number of categories
            if n_categories <= 6:
                chart_type = 'pie'
                reasoning = f"Pie chart recommended for {cat_col} ({n_categories} categories) showing {num_col} distribution"
            elif n_categories <= 12:
                chart_type = 'bar'
                reasoning = f"Bar chart recommended for comparing {num_col} across {n_categories} {cat_col} categories"
            else:
                chart_type = 'barh'
                reasoning = f"Horizontal bar chart recommended for {n_categories} categories (easier to read labels)"
            
            suggestions.append(ChartSuggestion(
                config=ChartConfig(
                    chart_type=chart_type,
                    title=f"{num_col} by {cat_col}",
                    group_by=cat_col,
                    value_column=num_col,
                ),
                reasoning=reasoning,
                confidence=0.9,
            ))
        
        # Suggestion 2: Line chart for time series (if date column exists)
        date_cols = self._df.select_dtypes(include=['datetime64']).columns.tolist()
        if not date_cols:
            # Check for columns with 'date', 'time', 'year', 'month' in name
            date_cols = [c for c in self._df.columns 
                        if any(d in c.lower() for d in ['date', 'time', 'year', 'month', 'fecha'])]
        
        if date_cols and numeric_cols:
            suggestions.append(ChartSuggestion(
                config=ChartConfig(
                    chart_type='line',
                    title=f"{numeric_cols[0]} over time",
                    group_by=date_cols[0],
                    value_column=numeric_cols[0],
                ),
                reasoning=f"Line chart recommended for showing {numeric_cols[0]} trends over {date_cols[0]}",
                confidence=0.85,
            ))
        
        # Suggestion 3: Scatter plot for two numeric columns
        if len(numeric_cols) >= 2:
            suggestions.append(ChartSuggestion(
                config=ChartConfig(
                    chart_type='scatter',
                    title=f"{numeric_cols[0]} vs {numeric_cols[1]}",
                    group_by=numeric_cols[0],
                    value_column=numeric_cols[1],
                ),
                reasoning=f"Scatter plot recommended to explore relationship between {numeric_cols[0]} and {numeric_cols[1]}",
                confidence=0.7,
            ))
        
        # Suggestion 4: Area chart for cumulative data
        if numeric_cols and categorical_cols:
            suggestions.append(ChartSuggestion(
                config=ChartConfig(
                    chart_type='area',
                    title=f"Cumulative {numeric_cols[0]}",
                    group_by=categorical_cols[0],
                    value_column=numeric_cols[0],
                ),
                reasoning=f"Area chart for showing cumulative {numeric_cols[0]} distribution",
                confidence=0.6,
            ))
        
        # Add context to conversation
        if context:
            self._add_to_context("user", f"Suggest charts for: {context}")
            self._add_to_context("assistant", f"Suggested {len(suggestions)} charts based on data analysis")
        
        return suggestions

    
    def prepare_report_data(
        self,
        description: str
    ) -> dict[str, Any]:
        """
        Prepare structured data for a report based on description.
        
        Analyzes the description and prepares appropriate data
        including suggested title, summary points, and chart configs.
        
        Args:
            description: Natural language description of desired report.
            
        Returns:
            Dictionary with:
            - title: Suggested report title
            - summary_points: Key points to include
            - charts: List of ChartConfig objects
            - data_filters: Suggested data filters
            - columns: Relevant columns for the report
        """
        # Add to context
        self._add_to_context("user", f"Prepare report: {description}")
        
        summary = self.get_data_summary()
        
        # Extract keywords from description
        description_lower = description.lower()
        
        # Determine relevant columns based on description
        relevant_cols = []
        for col in summary.columns:
            col_lower = col.lower()
            # Check if column name appears in description
            if col_lower in description_lower or any(
                word in col_lower for word in description_lower.split()
            ):
                relevant_cols.append(col)
        
        # If no specific columns found, use all
        if not relevant_cols:
            relevant_cols = summary.columns[:5]  # First 5 columns
        
        # Generate title from description
        title = self._generate_title(description)
        
        # Get chart suggestions
        chart_suggestions = self.suggest_charts(description)
        charts = [s.config for s in chart_suggestions[:3]]  # Top 3 suggestions
        
        # Generate summary points
        summary_points = self._generate_summary_points(description, summary)
        
        result = {
            "title": title,
            "summary_points": summary_points,
            "charts": charts,
            "data_filters": {},
            "columns": relevant_cols,
        }
        
        self._add_to_context("assistant", f"Prepared report data with {len(charts)} charts")
        
        return result
    
    def _generate_title(self, description: str) -> str:
        """Generate a report title from description."""
        # Simple title generation - capitalize first letter of each word
        words = description.split()[:6]  # First 6 words
        title = " ".join(words).title()
        
        # Add "Report" if not present
        if "report" not in title.lower() and "análisis" not in title.lower():
            title = f"{title} Report"
        
        return title
    
    def _generate_summary_points(
        self,
        description: str,
        summary: DataSummary
    ) -> list[str]:
        """Generate summary points for the report."""
        points = []
        
        # Data overview point
        points.append(
            f"Analysis based on {summary.shape[0]:,} records "
            f"with {summary.shape[1]} data fields"
        )
        
        # Numeric summary
        if summary.numeric_columns:
            for col in summary.numeric_columns[:2]:
                if col in self._df.columns:
                    total = self._df[col].sum()
                    avg = self._df[col].mean()
                    points.append(f"Total {col}: {total:,.2f} (avg: {avg:,.2f})")
        
        # Categorical summary
        if summary.categorical_columns:
            col = summary.categorical_columns[0]
            n_unique = self._df[col].nunique()
            points.append(f"{n_unique} unique {col} categories analyzed")
        
        return points
    
    def validate_query(self, query: str) -> tuple[bool, Optional[str]]:
        """
        Validate if a query is feasible with the current data.
        
        Checks if the query references columns that exist and
        if the requested operation is supported.
        
        Args:
            query: Natural language query to validate.
            
        Returns:
            Tuple of (is_valid, error_message).
            If valid, returns (True, None).
            If invalid, returns (False, description of issue).
        """
        query_lower = query.lower()
        summary = self.get_data_summary()
        
        # Check for column references
        referenced_cols = []
        for col in summary.columns:
            if col.lower() in query_lower:
                referenced_cols.append(col)
        
        # If specific columns mentioned, verify they exist
        if referenced_cols:
            missing = [c for c in referenced_cols if c not in self._df.columns]
            if missing:
                return (False, f"Columns not found: {', '.join(missing)}")
        
        # Check for aggregation keywords
        agg_keywords = ['sum', 'total', 'average', 'mean', 'count', 'max', 'min']
        has_aggregation = any(kw in query_lower for kw in agg_keywords)
        
        if has_aggregation and not summary.numeric_columns:
            return (False, "Aggregation requested but no numeric columns available")
        
        # Check for grouping keywords
        group_keywords = ['by', 'per', 'for each', 'grouped']
        has_grouping = any(kw in query_lower for kw in group_keywords)
        
        if has_grouping and not summary.categorical_columns:
            return (
                False,
                "Grouping requested but no categorical columns available for grouping"
            )
        
        return (True, None)
    
    def clear_context(self) -> None:
        """Clear the conversation context."""
        self._context = []
        logger.debug("Conversation context cleared")
    
    def _add_to_context(self, role: str, content: str) -> None:
        """
        Add a message to the conversation context.
        
        Args:
            role: Message role ('user' or 'assistant').
            content: Message content.
        """
        self._context.append({"role": role, "content": content})
        
        # Trim context if too long
        if len(self._context) > self.MAX_CONTEXT_MESSAGES:
            self._context = self._context[-self.MAX_CONTEXT_MESSAGES:]
    
    def get_context(self) -> list[dict[str, str]]:
        """
        Get the current conversation context.
        
        Returns:
            List of context messages with role and content.
        """
        return self._context.copy()
    
    def ask(self, query: str) -> str:
        """
        Ask a question about the data using LangChain.
        
        This method uses LangChain to process the query if available,
        otherwise falls back to basic analysis.
        
        Args:
            query: Natural language question about the data.
            
        Returns:
            Response string with analysis or answer.
            
        Raises:
            QueryError: If the query cannot be processed.
        """
        # Validate query first
        is_valid, error_msg = self.validate_query(query)
        if not is_valid:
            raise QueryError(
                user_message=f"Query validation failed: {error_msg}",
                internal_error=None
            )
        
        # Add to context
        self._add_to_context("user", query)
        
        # Try LangChain if available
        if self._langchain_available and self._chain is None:
            self._chain = self._build_chain()
        
        if self._chain is not None:
            try:
                summary = self.get_data_summary()
                response = self._chain.invoke({
                    "data_summary": str(summary),
                    "query": query
                })
                self._add_to_context("assistant", response)
                return response
            except Exception as e:
                logger.warning(f"LangChain query failed: {e}")
        
        # Fallback to basic analysis
        response = self._basic_analysis(query)
        self._add_to_context("assistant", response)
        return response
    
    def _basic_analysis(self, query: str) -> str:
        """
        Perform basic analysis without LangChain.
        
        Args:
            query: Query to analyze.
            
        Returns:
            Basic analysis response.
        """
        summary = self.get_data_summary()
        query_lower = query.lower()
        
        # Check for common query patterns
        if any(w in query_lower for w in ['column', 'field', 'variable']):
            return f"Available columns: {', '.join(summary.columns)}"
        
        if any(w in query_lower for w in ['type', 'dtype', 'format']):
            types_str = ", ".join(f"{k}: {v}" for k, v in summary.dtypes.items())
            return f"Column types: {types_str}"
        
        if any(w in query_lower for w in ['count', 'how many', 'number of']):
            return f"Dataset contains {summary.shape[0]:,} rows and {summary.shape[1]} columns"
        
        if any(w in query_lower for w in ['summary', 'overview', 'describe']):
            return (
                f"Data Overview:\n"
                f"- Rows: {summary.shape[0]:,}\n"
                f"- Columns: {summary.shape[1]}\n"
                f"- Numeric columns: {', '.join(summary.numeric_columns)}\n"
                f"- Categorical columns: {', '.join(summary.categorical_columns)}"
            )
        
        # Default response
        return (
            f"I analyzed your query about the data. "
            f"The dataset has {summary.shape[0]:,} rows with columns: "
            f"{', '.join(summary.columns[:5])}{'...' if len(summary.columns) > 5 else ''}"
        )
    
    @property
    def dataframe(self) -> pd.DataFrame:
        """Get the underlying DataFrame."""
        return self._df
    
    @property
    def has_langchain(self) -> bool:
        """Check if LangChain is available."""
        return self._langchain_available
