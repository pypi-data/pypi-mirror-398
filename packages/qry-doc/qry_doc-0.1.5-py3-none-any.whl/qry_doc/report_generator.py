"""
PDF report generation for qry-doc.

This module provides the ReportGenerator class for creating
professional PDF reports using ReportLab/Platypus.
"""
from pathlib import Path
from typing import Any, Optional, Union

import pandas as pd
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
    PageBreak,
    BaseDocTemplate,
    Frame,
    PageTemplate,
)
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

from qry_doc.report_template import ReportTemplate, DEFAULT_TEMPLATE, SectionType, SectionConfig
from qry_doc.exceptions import ReportError, ValidationError
from qry_doc.validators import OutputValidator
from qry_doc.asset_manager import AssetManager

# Import for type checking
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from qry_doc.chart_config import ChartConfig

import logging

logger = logging.getLogger(__name__)


# Default section order when no sections are configured
DEFAULT_SECTIONS = [
    SectionConfig(SectionType.SUMMARY),
    SectionConfig(SectionType.CHART),
    SectionConfig(SectionType.DATA),
]


class ReportGenerator:
    """
    Generates PDF reports using ReportLab/Platypus.
    
    Features:
    - Automatic table column width adjustment
    - Chart/image embedding
    - Custom template support
    - Professional styling
    """
    
    # Minimum column width in points
    MIN_COL_WIDTH = 30
    # Maximum characters before text wrapping
    MAX_CELL_CHARS = 50
    # Font size reduction steps for wide tables
    FONT_SIZE_STEPS = [10, 9, 8, 7, 6]
    
    def __init__(
        self,
        output_path: Union[str, Path],
        template: Optional[ReportTemplate] = None
    ) -> None:
        """
        Initialize the report generator.
        
        Args:
            output_path: Path for the output PDF file.
            template: Optional ReportTemplate for styling.
        """
        self.output_path = Path(output_path)
        self.template = template or DEFAULT_TEMPLATE
        self.story: list[Any] = []
        self.styles = self._create_styles()
        self._header_footer_call_count = 0
        self._cover_image_path: Optional[Path] = None
        self._is_cover_page = False
    
    def _create_styles(self) -> dict[str, ParagraphStyle]:
        """Create custom paragraph styles based on template."""
        base_styles = getSampleStyleSheet()
        
        # Register custom fonts and get font names to use
        title_font, body_font = self.template.register_custom_fonts()
        
        # Custom title style
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=base_styles['Title'],
            fontName=title_font,
            fontSize=24,
            textColor=self.template.primary_color_obj,
            spaceAfter=20,
            alignment=TA_CENTER,
        )
        
        # Custom heading style
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=base_styles['Heading2'],
            fontName=title_font,
            fontSize=14,
            textColor=self.template.primary_color_obj,
            spaceBefore=15,
            spaceAfter=10,
        )
        
        # Custom body style
        body_style = ParagraphStyle(
            'CustomBody',
            parent=base_styles['Normal'],
            fontName=body_font,
            fontSize=10,
            leading=14,
            alignment=TA_JUSTIFY,
            spaceAfter=10,
        )
        
        # Store the resolved font names for table styling
        self._title_font = title_font
        self._body_font = body_font
        
        return {
            'Title': title_style,
            'Heading': heading_style,
            'Body': body_style,
            'Normal': base_styles['Normal'],
        }
    
    def build(
        self,
        title: str,
        summary: str,
        chart_path: Optional[Path] = None,
        dataframe: Optional[pd.DataFrame] = None
    ) -> None:
        """
        Build and save the PDF report.
        
        Args:
            title: Report title.
            summary: Executive summary text.
            chart_path: Optional path to chart image.
            dataframe: Optional DataFrame to render as table.
            
        Raises:
            ReportError: If report generation fails.
            ValidationError: If cover image path is invalid.
        """
        try:
            # Reset story and state
            self.story = []
            self._header_footer_call_count = 0
            self._cover_image_path = None
            self._is_cover_page = False
            
            # Add cover page if configured
            if self.template.cover_image_path is not None:
                self._add_cover_page(self.template.cover_image_path)
            
            # Add title
            self.story.append(Paragraph(title, self.styles['Title']))
            self.story.append(Spacer(1, 20))
            
            # Add summary section
            self.story.append(Paragraph("Análisis Ejecutivo", self.styles['Heading']))
            
            # Split summary into paragraphs
            for para in summary.split('\n\n'):
                if para.strip():
                    self.story.append(Paragraph(para.strip(), self.styles['Body']))
            
            self.story.append(Spacer(1, 15))
            
            # Add chart if provided
            if chart_path:
                self._add_chart(chart_path)
            
            # Add table if provided
            if dataframe is not None:
                self._add_table(dataframe)
            
            # Build the document
            self._build_document()
            
        except ValidationError:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            sanitized = OutputValidator.sanitize_error_message(e)
            raise ReportError(
                user_message=f"Error al generar el reporte: {sanitized}",
                internal_error=e
            )
    
    def _add_chart(self, chart_path: Path) -> None:
        """Add a chart image to the report."""
        # Verify file exists
        is_valid, error_msg = OutputValidator.verify_file_exists(chart_path)
        if not is_valid:
            # Skip chart if file doesn't exist
            return
        
        try:
            # Calculate image dimensions to fit content width
            max_width = self.template.content_width
            max_height = 300  # Maximum height in points
            
            img = Image(str(chart_path))
            
            # Scale to fit
            img_width, img_height = img.imageWidth, img.imageHeight
            scale = min(max_width / img_width, max_height / img_height, 1.0)
            
            img.drawWidth = img_width * scale
            img.drawHeight = img_height * scale
            
            self.story.append(Paragraph("Visualización", self.styles['Heading']))
            self.story.append(img)
            self.story.append(Spacer(1, 15))
            
        except Exception:
            # Skip chart if it can't be loaded
            pass
    
    def _add_table(self, df: pd.DataFrame) -> None:
        """Add a DataFrame as a table to the report."""
        # Validate DataFrame
        is_valid, error_msg = OutputValidator.validate_dataframe(df)
        if not is_valid:
            return
        
        self.story.append(Paragraph("Datos", self.styles['Heading']))
        
        # Create table with auto-adjusted widths
        table = self._auto_adjust_table(df)
        self.story.append(table)
        self.story.append(Spacer(1, 15))
    
    def _add_cover_page(self, cover_image_path: Path) -> None:
        """
        Mark that a cover page should be added.
        
        The cover image will be drawn directly on the canvas (not via Platypus)
        to avoid frame size restrictions. The actual drawing happens in
        _draw_cover_on_canvas which is called from the page template.
        
        Args:
            cover_image_path: Path to the cover image file.
            
        Raises:
            ValidationError: If the cover image path is invalid.
        """
        # Validate cover image path
        is_valid, error_msg = AssetManager.validate_image_path(cover_image_path)
        if not is_valid:
            raise ValidationError(
                user_message=f"Cover image not found: {cover_image_path}",
                internal_error=None
            )
        
        # Store the path - actual drawing happens in _draw_cover_on_canvas
        self._cover_image_path = cover_image_path
        self._is_cover_page = True
        
        # Add a PageBreak to create the cover page, content starts on page 2
        self.story.append(PageBreak())
    
    def _draw_cover_on_canvas(self, canvas: Any) -> None:
        """
        Draw the cover image directly on the canvas.
        
        Uses the Canvas method (drawImage) instead of Platypus flowables
        to avoid frame size restrictions. The image is scaled to cover
        the full page while maintaining aspect ratio.
        
        Args:
            canvas: ReportLab canvas object.
        """
        if self._cover_image_path is None:
            return
        
        try:
            from reportlab.lib.utils import ImageReader
            
            # Get image dimensions
            img_reader = ImageReader(str(self._cover_image_path))
            orig_width, orig_height = img_reader.getSize()
            
            # Use full page dimensions (no margins for cover)
            page_width = self.template.page_width
            page_height = self.template.page_height
            
            # Scale to cover the full page while maintaining aspect ratio
            width_scale = page_width / orig_width
            height_scale = page_height / orig_height
            # Use max to ensure the image covers the entire page
            scale = max(width_scale, height_scale)
            
            final_width = orig_width * scale
            final_height = orig_height * scale
            
            # Center the image (may overflow on one axis)
            x = (page_width - final_width) / 2
            y = (page_height - final_height) / 2
            
            # Draw directly on canvas - full page, no margins
            canvas.saveState()
            canvas.drawImage(
                str(self._cover_image_path),
                x, y,
                width=final_width,
                height=final_height,
                preserveAspectRatio=True,
                mask='auto'
            )
            canvas.restoreState()
            
        except Exception as e:
            raise ValidationError(
                user_message=f"Invalid cover image format. Supported: PNG, JPG, JPEG",
                internal_error=e
            )
    
    def _get_effective_sections(self) -> list[SectionConfig]:
        """
        Get the effective list of sections to render.
        
        Returns the configured sections if any, otherwise returns the
        default section order: SUMMARY, CHART, DATA.
        
        Returns:
            List of SectionConfig objects to render.
        """
        if self.template.sections:
            return [s for s in self.template.sections if s.enabled]
        return DEFAULT_SECTIONS
    
    def _render_section(
        self,
        section: SectionConfig,
        title: str,
        summary: str,
        chart_path: Optional[Path],
        dataframe: Optional[pd.DataFrame],
        custom_sections: Optional[dict[str, str]]
    ) -> bool:
        """
        Render a single section based on its type.
        
        Args:
            section: The section configuration to render.
            title: Report title (for SUMMARY section).
            summary: Summary text (for SUMMARY section).
            chart_path: Path to chart image (for CHART section).
            dataframe: DataFrame to render (for DATA section).
            custom_sections: Dict of custom section content by name.
            
        Returns:
            True if section was rendered, False if skipped.
        """
        if section.section_type == SectionType.COVER:
            # Cover is handled separately before sections
            return False
        
        elif section.section_type == SectionType.SUMMARY:
            # Add title and summary
            self.story.append(Paragraph(title, self.styles['Title']))
            self.story.append(Spacer(1, 20))
            self.story.append(Paragraph("Análisis Ejecutivo", self.styles['Heading']))
            for para in summary.split('\n\n'):
                if para.strip():
                    self.story.append(Paragraph(para.strip(), self.styles['Body']))
            self.story.append(Spacer(1, 15))
            return True
        
        elif section.section_type == SectionType.CHART:
            if chart_path is not None:
                self._add_chart(chart_path)
                return True
            return False
        
        elif section.section_type == SectionType.DATA:
            if dataframe is not None:
                self._add_table(dataframe)
                return True
            return False
        
        elif section.section_type == SectionType.CUSTOM:
            if section.custom_content:
                self._add_custom_section(section.custom_content)
                return True
            return False
        
        return False
    
    def _add_custom_section(self, content: str) -> None:
        """
        Add a custom section with arbitrary paragraph content.
        
        Args:
            content: The text content to render as paragraphs.
        """
        for para in content.split('\n\n'):
            if para.strip():
                self.story.append(Paragraph(para.strip(), self.styles['Body']))
        self.story.append(Spacer(1, 15))
    
    def build_with_sections(
        self,
        title: str,
        summary: str,
        chart_path: Optional[Path] = None,
        dataframe: Optional[pd.DataFrame] = None,
        custom_sections: Optional[dict[str, str]] = None
    ) -> None:
        """
        Build and save the PDF report using section-based rendering.
        
        This method renders sections in the order specified by the template.
        If no sections are configured, uses the default order: SUMMARY, CHART, DATA.
        
        Args:
            title: Report title.
            summary: Executive summary text.
            chart_path: Optional path to chart image.
            dataframe: Optional DataFrame to render as table.
            custom_sections: Optional dict of custom section content.
            
        Raises:
            ReportError: If report generation fails.
            ValidationError: If cover image path is invalid.
        """
        try:
            # Reset story and state
            self.story = []
            self._header_footer_call_count = 0
            self._cover_image_path = None
            self._is_cover_page = False
            
            # Get effective sections
            sections = self._get_effective_sections()
            
            # Check if COVER section is in the list
            has_cover_section = any(s.section_type == SectionType.COVER for s in sections)
            
            # Add cover page if configured (either via template or section)
            if self.template.cover_image_path is not None:
                if has_cover_section or not sections:
                    self._add_cover_page(self.template.cover_image_path)
            
            # Render each section in order
            for section in sections:
                self._render_section(
                    section, title, summary, chart_path, dataframe, custom_sections
                )
            
            # Build the document
            self._build_document()
            
        except ValidationError:
            raise
        except Exception as e:
            sanitized = OutputValidator.sanitize_error_message(e)
            raise ReportError(
                user_message=f"Error al generar el reporte: {sanitized}",
                internal_error=e
            )
    
    def _auto_adjust_table(self, df: pd.DataFrame) -> Table:
        """
        Create a table with automatically adjusted column widths.
        
        Args:
            df: DataFrame to convert to table.
            
        Returns:
            ReportLab Table object.
        """
        # Convert DataFrame to list of lists
        data = [df.columns.tolist()] + df.values.tolist()
        
        # Convert all values to strings and wrap long text
        wrapped_data = []
        for row in data:
            wrapped_row = []
            for cell in row:
                cell_str = str(cell) if cell is not None else ""
                # Wrap long text in Paragraph for text wrapping
                if len(cell_str) > self.MAX_CELL_CHARS:
                    wrapped_row.append(Paragraph(cell_str, self.styles['Normal']))
                else:
                    wrapped_row.append(cell_str)
            wrapped_data.append(wrapped_row)
        
        # Calculate column widths
        col_widths = self._calculate_column_widths(df, self.template.content_width)
        
        # Determine font size based on table width
        font_size = self._determine_font_size(col_widths, self.template.content_width)
        
        # Create table
        table = Table(wrapped_data, colWidths=col_widths, repeatRows=1)
        
        # Apply styling
        style = TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), self.template.primary_color_obj),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('FONTNAME', (0, 0), (-1, 0), self._title_font),
            ('FONTSIZE', (0, 0), (-1, 0), font_size),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            
            # Body styling
            ('FONTNAME', (0, 1), (-1, -1), self._body_font),
            ('FONTSIZE', (0, 1), (-1, -1), font_size - 1),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
            ('TOPPADDING', (0, 1), (-1, -1), 5),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor("#f5f5f5")]),
            
            # Alignment
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ])
        
        table.setStyle(style)
        return table
    
    def _calculate_column_widths(
        self,
        df: pd.DataFrame,
        available_width: float
    ) -> list[float]:
        """
        Calculate optimal column widths based on content.
        
        Args:
            df: DataFrame to analyze.
            available_width: Available width in points.
            
        Returns:
            List of column widths in points.
        """
        n_cols = len(df.columns)
        
        # Calculate content-based widths
        widths = []
        for col in df.columns:
            # Get max length in column (including header)
            max_len = max(
                len(str(col)),
                df[col].astype(str).str.len().max() if len(df) > 0 else 0
            )
            # Estimate width (roughly 7 points per character)
            estimated_width = max(max_len * 7, self.MIN_COL_WIDTH)
            widths.append(estimated_width)
        
        # Scale to fit available width
        total_width = sum(widths)
        if total_width > available_width:
            scale = available_width / total_width
            widths = [max(w * scale, self.MIN_COL_WIDTH) for w in widths]
        
        # Distribute remaining space
        total_width = sum(widths)
        if total_width < available_width:
            extra = (available_width - total_width) / n_cols
            widths = [w + extra for w in widths]
        
        return widths
    
    def _determine_font_size(
        self,
        col_widths: list[float],
        available_width: float
    ) -> int:
        """
        Determine appropriate font size based on table width.
        
        Args:
            col_widths: List of column widths.
            available_width: Available width in points.
            
        Returns:
            Font size in points.
        """
        total_width = sum(col_widths)
        
        # If table fits comfortably, use default size
        if total_width <= available_width * 0.9:
            return self.FONT_SIZE_STEPS[0]
        
        # Reduce font size for wider tables
        ratio = total_width / available_width
        if ratio > 1.5:
            return self.FONT_SIZE_STEPS[-1]
        elif ratio > 1.3:
            return self.FONT_SIZE_STEPS[-2]
        elif ratio > 1.1:
            return self.FONT_SIZE_STEPS[-3]
        else:
            return self.FONT_SIZE_STEPS[1]
    
    def _build_document(self) -> None:
        """Build the final PDF document with template."""
        # Ensure parent directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create document with custom page template
        doc = BaseDocTemplate(
            str(self.output_path),
            pagesize=self.template.page_size,
            leftMargin=self.template.margin_left,
            rightMargin=self.template.margin_right,
            topMargin=self.template.margin_top + self.template.header_height,
            bottomMargin=self.template.margin_bottom + self.template.footer_height,
        )
        
        # Create frame for content (no internal padding)
        frame = Frame(
            self.template.margin_left,
            self.template.margin_bottom + self.template.footer_height,
            self.template.content_width,
            self.template.content_height,
            id='normal',
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0
        )
        
        # Track if we're on the cover page
        is_first_page = [True]  # Use list to allow modification in closure
        
        # Create page template with header/footer
        def on_page(canvas, doc):
            self._header_footer_call_count += 1
            
            # Check if this is the cover page
            if is_first_page[0] and self._is_cover_page:
                # Draw cover image directly on canvas
                self._draw_cover_on_canvas(canvas)
                is_first_page[0] = False
                # Don't draw header/footer on cover page
                return
            
            is_first_page[0] = False
            self.template.draw_header(canvas, doc)
            self.template.draw_footer(canvas, doc)
        
        page_template = PageTemplate(
            id='main',
            frames=[frame],
            onPage=on_page
        )
        
        doc.addPageTemplates([page_template])
        
        # Build document
        doc.build(self.story)
    
    @property
    def header_footer_calls(self) -> int:
        """Get the number of times header/footer were drawn (equals page count)."""
        return self._header_footer_call_count

    def _render_charts(
        self,
        charts: list["ChartConfig"],
        df: pd.DataFrame,
        temp_dir: Path
    ) -> list[Path]:
        """
        Generate and return paths to all chart images.
        
        Renders each chart configuration, logging warnings for failures
        and continuing with remaining charts (fault tolerance).
        
        Args:
            charts: List of ChartConfig objects to render.
            df: DataFrame to use for chart data.
            temp_dir: Temporary directory for chart images.
            
        Returns:
            List of paths to successfully generated chart images.
        """
        from qry_doc.chart_generator import ChartGenerator
        
        chart_paths: list[Path] = []
        
        for i, chart_config in enumerate(charts):
            try:
                chart_path = temp_dir / f"chart_{i}_{chart_config.chart_type}.png"
                
                # Determine data for chart
                chart_df = df
                
                # If group_by and value_column are specified, aggregate
                if chart_config.group_by and chart_config.value_column:
                    if (chart_config.group_by in df.columns and 
                        chart_config.value_column in df.columns):
                        chart_df = df.groupby(chart_config.group_by)[
                            chart_config.value_column
                        ].sum().reset_index()
                
                # Generate the chart
                generated_path = ChartGenerator.generate(
                    df=chart_df,
                    output_path=chart_path,
                    chart_type=chart_config.chart_type,
                    title=chart_config.title,
                    x_column=chart_config.group_by,
                    y_column=chart_config.value_column,
                    figsize=chart_config.figsize,
                    color=chart_config.color,
                )
                
                chart_paths.append(generated_path)
                logger.debug(f"Generated chart {i + 1}: {chart_config.title}")
                
            except Exception as e:
                # Log warning and continue with remaining charts
                logger.warning(
                    f"Failed to generate chart {i + 1} ({chart_config.title}): {e}"
                )
                continue
        
        return chart_paths
    
    def _add_charts(self, chart_paths: list[Path]) -> None:
        """
        Add multiple charts to the report story.
        
        Adds each chart with its own heading and handles page breaks
        automatically when charts exceed available space.
        
        Args:
            chart_paths: List of paths to chart images.
        """
        for i, chart_path in enumerate(chart_paths):
            # Add page break before chart if not the first one
            if i > 0:
                self.story.append(PageBreak())
            
            self._add_chart(chart_path)
    
    def build_with_charts(
        self,
        title: str,
        summary: str,
        charts: list["ChartConfig"],
        dataframe: pd.DataFrame,
        temp_dir: Optional[Path] = None,
    ) -> None:
        """
        Build and save the PDF report with multiple charts.
        
        This method renders a report with multiple charts in sequence,
        handling page breaks automatically.
        
        Args:
            title: Report title.
            summary: Executive summary text.
            charts: List of ChartConfig objects defining charts to include.
            dataframe: DataFrame to use for chart data and table.
            temp_dir: Optional temporary directory for chart images.
                     If not provided, creates a temporary directory.
            
        Raises:
            ReportError: If report generation fails.
            ValidationError: If configuration is invalid.
        """
        import tempfile
        
        try:
            # Reset story and state
            self.story = []
            self._header_footer_call_count = 0
            self._cover_image_path = None
            self._is_cover_page = False
            
            # Add cover page if configured
            if self.template.cover_image_path is not None:
                self._add_cover_page(self.template.cover_image_path)
            
            # Add title
            self.story.append(Paragraph(title, self.styles['Title']))
            self.story.append(Spacer(1, 20))
            
            # Add summary section
            self.story.append(Paragraph("Análisis Ejecutivo", self.styles['Heading']))
            for para in summary.split('\n\n'):
                if para.strip():
                    self.story.append(Paragraph(para.strip(), self.styles['Body']))
            self.story.append(Spacer(1, 15))
            
            # Generate and add charts
            if charts:
                # Use provided temp_dir or create one
                if temp_dir is None:
                    with tempfile.TemporaryDirectory(prefix="qry_doc_charts_") as tmp:
                        chart_paths = self._render_charts(charts, dataframe, Path(tmp))
                        if chart_paths:
                            self._add_charts(chart_paths)
                else:
                    chart_paths = self._render_charts(charts, dataframe, temp_dir)
                    if chart_paths:
                        self._add_charts(chart_paths)
            
            # Add table if dataframe provided
            if dataframe is not None and not dataframe.empty:
                self.story.append(PageBreak())
                self._add_table(dataframe)
            
            # Build the document
            self._build_document()
            
        except ValidationError:
            raise
        except Exception as e:
            sanitized = OutputValidator.sanitize_error_message(e)
            raise ReportError(
                user_message=f"Error al generar el reporte: {sanitized}",
                internal_error=e
            )
    
    def build_with_sections_and_charts(
        self,
        title: str,
        summary: str,
        charts: Optional[list["ChartConfig"]] = None,
        dataframe: Optional[pd.DataFrame] = None,
        custom_sections: Optional[dict[str, str]] = None,
        temp_dir: Optional[Path] = None,
    ) -> None:
        """
        Build and save the PDF report using section-based rendering with multiple charts.
        
        This method combines section-based rendering with multi-chart support.
        Charts are rendered in the CHART section(s) in the order specified.
        
        Args:
            title: Report title.
            summary: Executive summary text.
            charts: Optional list of ChartConfig objects.
            dataframe: Optional DataFrame to render as table.
            custom_sections: Optional dict of custom section content.
            temp_dir: Optional temporary directory for chart images.
            
        Raises:
            ReportError: If report generation fails.
            ValidationError: If cover image path is invalid.
        """
        import tempfile
        
        try:
            # Reset story and state
            self.story = []
            self._header_footer_call_count = 0
            self._cover_image_path = None
            self._is_cover_page = False
            
            # Get effective sections
            sections = self._get_effective_sections()
            
            # Check if COVER section is in the list
            has_cover_section = any(s.section_type == SectionType.COVER for s in sections)
            
            # Add cover page if configured
            if self.template.cover_image_path is not None:
                if has_cover_section or not sections:
                    self._add_cover_page(self.template.cover_image_path)
            
            # Generate chart images if charts provided
            chart_paths: list[Path] = []
            temp_dir_context = None
            
            if charts:
                if temp_dir is None:
                    temp_dir_context = tempfile.TemporaryDirectory(prefix="qry_doc_charts_")
                    temp_dir = Path(temp_dir_context.name)
                
                chart_paths = self._render_charts(charts, dataframe or pd.DataFrame(), temp_dir)
            
            try:
                # Track which chart we're on
                chart_index = [0]
                
                # Render each section in order
                for section in sections:
                    if section.section_type == SectionType.CHART:
                        # Render next chart if available
                        if chart_index[0] < len(chart_paths):
                            self._add_chart(chart_paths[chart_index[0]])
                            chart_index[0] += 1
                    else:
                        self._render_section(
                            section, title, summary, None, dataframe, custom_sections
                        )
                
                # Add any remaining charts
                while chart_index[0] < len(chart_paths):
                    self.story.append(PageBreak())
                    self._add_chart(chart_paths[chart_index[0]])
                    chart_index[0] += 1
                
                # Build the document
                self._build_document()
                
            finally:
                # Clean up temp directory if we created it
                if temp_dir_context is not None:
                    temp_dir_context.cleanup()
            
        except ValidationError:
            raise
        except Exception as e:
            sanitized = OutputValidator.sanitize_error_message(e)
            raise ReportError(
                user_message=f"Error al generar el reporte: {sanitized}",
                internal_error=e
            )
