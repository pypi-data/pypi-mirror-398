"""
Template builder for fluent PDF report configuration.

This module provides TemplateBuilder for constructing ReportTemplate
instances using a chainable fluent API.
"""
from pathlib import Path
from typing import Any, Optional, Union, TYPE_CHECKING

from reportlab.lib.pagesizes import letter, A4

from qry_doc.report_template import (
    ReportTemplate,
    SectionConfig,
    SectionType,
    LogoPosition,
    PageSize,
)
from qry_doc.report_preset import ReportPreset, ReportPresetType
from qry_doc.text_element import is_valid_hex_color
from qry_doc.exceptions import ValidationError

if TYPE_CHECKING:
    from qry_doc.chart_config import ChartConfig


# Maximum number of charts allowed per report
MAX_CHARTS_PER_REPORT = 10


class TemplateBuilder:
    """
    Fluent builder for constructing ReportTemplate instances.
    
    Provides a chainable API for configuring all aspects of a report
    template including colors, fonts, margins, header, footer, and sections.
    
    Example:
        ```python
        template = (
            TemplateBuilder()
            .with_colors(primary="#003366", secondary="#0066CC")
            .with_fonts(title_font="Helvetica-Bold", body_font="Helvetica")
            .with_margins(top=72, bottom=72, left=72, right=72)
            .with_header(logo_path="logo.png", height=50)
            .with_footer(logo_position=LogoPosition.BOTTOM_RIGHT)
            .with_sections([
                SectionConfig(SectionType.COVER),
                SectionConfig(SectionType.SUMMARY),
                SectionConfig(SectionType.CHART),
                SectionConfig(SectionType.DATA),
            ])
            .build()
        )
        ```
    """
    
    def __init__(self) -> None:
        """Initialize the TemplateBuilder with default values."""
        self._config: dict[str, Any] = {
            "primary_color": "#1a1a2e",
            "title_font": "Helvetica-Bold",
            "body_font": "Helvetica",
            "page_size": letter,
            "margin_top": 72.0,
            "margin_bottom": 72.0,
            "margin_left": 72.0,
            "margin_right": 72.0,
            "header_height": 50.0,
            "footer_height": 30.0,
            "sections": [],
        }
        self._charts: list["ChartConfig"] = []  # Will hold ChartConfig objects
    
    @classmethod
    def from_preset(cls, preset_type: ReportPresetType) -> "TemplateBuilder":
        """
        Initialize a TemplateBuilder from a ReportPreset.
        
        Args:
            preset_type: The type of preset to use as base configuration.
            
        Returns:
            TemplateBuilder initialized with preset values.
            
        Example:
            ```python
            template = (
                TemplateBuilder.from_preset(ReportPresetType.FINANCIAL)
                .with_margins(top=100)  # Override just the top margin
                .build()
            )
            ```
        """
        preset = ReportPreset.get(preset_type)
        builder = cls()
        
        # Apply preset values
        builder._config["primary_color"] = preset.primary_color
        builder._config["title_font"] = preset.title_font
        builder._config["body_font"] = preset.body_font
        builder._config["sections"] = list(preset.default_sections)
        
        return builder
    
    def with_colors(
        self,
        primary: str,
        secondary: Optional[str] = None,
    ) -> "TemplateBuilder":
        """
        Configure colors for the template.
        
        Args:
            primary: Primary hex color for headings and accents.
            secondary: Optional secondary hex color (stored for reference).
            
        Returns:
            Self for method chaining.
            
        Raises:
            ValidationError: If color is not a valid hex format.
        """
        if not is_valid_hex_color(primary):
            raise ValidationError(
                user_message=f"Invalid primary color format: '{primary}'. Use format like '#FF0000'.",
                internal_error=None
            )
        
        if secondary is not None and not is_valid_hex_color(secondary):
            raise ValidationError(
                user_message=f"Invalid secondary color format: '{secondary}'. Use format like '#FF0000'.",
                internal_error=None
            )
        
        self._config["primary_color"] = primary.upper()
        if secondary is not None:
            self._config["secondary_color"] = secondary.upper()
        
        return self
    
    def with_fonts(
        self,
        title_font: str,
        body_font: Optional[str] = None,
    ) -> "TemplateBuilder":
        """
        Configure fonts for the template.
        
        Args:
            title_font: Font family for titles and headings.
            body_font: Optional font family for body text. Defaults to title_font.
            
        Returns:
            Self for method chaining.
        """
        self._config["title_font"] = title_font
        self._config["body_font"] = body_font if body_font is not None else title_font
        
        return self
    
    def with_margins(
        self,
        top: Optional[float] = None,
        bottom: Optional[float] = None,
        left: Optional[float] = None,
        right: Optional[float] = None,
    ) -> "TemplateBuilder":
        """
        Configure page margins.
        
        Args:
            top: Top margin in points. Default 72.0 (1 inch).
            bottom: Bottom margin in points. Default 72.0.
            left: Left margin in points. Default 72.0.
            right: Right margin in points. Default 72.0.
            
        Returns:
            Self for method chaining.
            
        Raises:
            ValidationError: If any margin is negative.
        """
        margins = {
            "margin_top": top,
            "margin_bottom": bottom,
            "margin_left": left,
            "margin_right": right,
        }
        
        for name, value in margins.items():
            if value is not None:
                if value < 0:
                    raise ValidationError(
                        user_message=f"{name} cannot be negative, got {value}",
                        internal_error=None
                    )
                self._config[name] = value
        
        return self
    
    def with_page_size(self, page_size: PageSize) -> "TemplateBuilder":
        """
        Configure page size.
        
        Args:
            page_size: Page dimensions as (width, height) tuple in points.
                      Use letter (612x792) or A4 (595x842) from reportlab.
            
        Returns:
            Self for method chaining.
        """
        self._config["page_size"] = page_size
        return self
    
    def with_header(
        self,
        logo_path: Optional[Union[str, Path]] = None,
        height: Optional[float] = None,
    ) -> "TemplateBuilder":
        """
        Configure the header.
        
        Args:
            logo_path: Path to logo image for header.
            height: Header height in points. Default 50.0.
            
        Returns:
            Self for method chaining.
            
        Raises:
            ValidationError: If height is negative.
        """
        if logo_path is not None:
            self._config["logo_path"] = Path(logo_path) if isinstance(logo_path, str) else logo_path
        
        if height is not None:
            if height < 0:
                raise ValidationError(
                    user_message=f"header height cannot be negative, got {height}",
                    internal_error=None
                )
            self._config["header_height"] = height
        
        return self
    
    def with_footer(
        self,
        logo_path: Optional[Union[str, Path]] = None,
        logo_position: Optional[LogoPosition] = None,
        logo_enabled: Optional[bool] = None,
        logo_width: Optional[float] = None,
        logo_height: Optional[float] = None,
        height: Optional[float] = None,
    ) -> "TemplateBuilder":
        """
        Configure the footer.
        
        Args:
            logo_path: Path to footer logo image.
            logo_position: Position of footer logo.
            logo_enabled: Whether to show footer logo.
            logo_width: Width of footer logo in points.
            logo_height: Height of footer logo in points.
            height: Footer height in points. Default 30.0.
            
        Returns:
            Self for method chaining.
            
        Raises:
            ValidationError: If height or logo dimensions are negative.
        """
        if logo_path is not None:
            self._config["footer_logo_path"] = Path(logo_path) if isinstance(logo_path, str) else logo_path
        
        if logo_position is not None:
            self._config["footer_logo_position"] = logo_position
        
        if logo_enabled is not None:
            self._config["footer_logo_enabled"] = logo_enabled
        
        if logo_width is not None:
            if logo_width < 0:
                raise ValidationError(
                    user_message=f"footer logo_width cannot be negative, got {logo_width}",
                    internal_error=None
                )
            self._config["footer_logo_width"] = logo_width
        
        if logo_height is not None:
            if logo_height < 0:
                raise ValidationError(
                    user_message=f"footer logo_height cannot be negative, got {logo_height}",
                    internal_error=None
                )
            self._config["footer_logo_height"] = logo_height
        
        if height is not None:
            if height < 0:
                raise ValidationError(
                    user_message=f"footer height cannot be negative, got {height}",
                    internal_error=None
                )
            self._config["footer_height"] = height
        
        return self
    
    def with_sections(self, sections: list[SectionConfig]) -> "TemplateBuilder":
        """
        Configure report sections.
        
        Args:
            sections: List of SectionConfig objects defining report structure.
            
        Returns:
            Self for method chaining.
        """
        self._config["sections"] = list(sections)
        return self
    
    def with_cover(self, cover_image_path: Union[str, Path]) -> "TemplateBuilder":
        """
        Configure cover page image.
        
        Args:
            cover_image_path: Path to cover page image.
            
        Returns:
            Self for method chaining.
        """
        self._config["cover_image_path"] = Path(cover_image_path) if isinstance(cover_image_path, str) else cover_image_path
        return self
    
    def with_custom_fonts(
        self,
        title_font_path: Optional[Union[str, Path]] = None,
        body_font_path: Optional[Union[str, Path]] = None,
    ) -> "TemplateBuilder":
        """
        Configure custom TTF/OTF fonts.
        
        Args:
            title_font_path: Path to custom title font file.
            body_font_path: Path to custom body font file.
            
        Returns:
            Self for method chaining.
        """
        if title_font_path is not None:
            self._config["custom_title_font_path"] = Path(title_font_path) if isinstance(title_font_path, str) else title_font_path
        
        if body_font_path is not None:
            self._config["custom_body_font_path"] = Path(body_font_path) if isinstance(body_font_path, str) else body_font_path
        
        return self
    
    def with_charts(self, charts: list["ChartConfig"]) -> "TemplateBuilder":
        """
        Configure charts for the report.
        
        Args:
            charts: List of ChartConfig objects defining charts to include.
            
        Returns:
            Self for method chaining.
            
        Raises:
            ValidationError: If more than 10 charts are provided or if any
                           chart configuration is invalid.
        """
        # Import here to avoid circular imports
        from qry_doc.chart_config import validate_chart_list, MAX_CHARTS_PER_REPORT as CHART_MAX
        
        if len(charts) > MAX_CHARTS_PER_REPORT:
            raise ValidationError(
                user_message=f"Maximum {MAX_CHARTS_PER_REPORT} charts per report, got {len(charts)}",
                internal_error=None
            )
        
        # Validate each chart configuration
        is_valid, error_msg = validate_chart_list(charts)
        if not is_valid:
            raise ValidationError(
                user_message=error_msg or "Invalid chart configuration",
                internal_error=None
            )
        
        self._charts = list(charts)
        return self
    
    def build(self) -> ReportTemplate:
        """
        Build and return the configured ReportTemplate.
        
        Validates all configuration and returns a ReportTemplate instance.
        
        Returns:
            ReportTemplate with all configured values.
            
        Raises:
            ValidationError: If configuration is invalid.
        """
        # Validate configuration
        self._validate()
        
        # Build template with only valid ReportTemplate fields
        template_fields = {
            "logo_path",
            "primary_color",
            "title_font",
            "body_font",
            "page_size",
            "margin_top",
            "margin_bottom",
            "margin_left",
            "margin_right",
            "header_height",
            "footer_height",
            "cover_image_path",
            "footer_logo_path",
            "footer_logo_enabled",
            "footer_logo_position",
            "footer_logo_width",
            "footer_logo_height",
            "custom_title_font_path",
            "custom_body_font_path",
            "sections",
        }
        
        template_config = {
            k: v for k, v in self._config.items()
            if k in template_fields
        }
        
        return ReportTemplate(**template_config)
    
    def _validate(self) -> None:
        """
        Validate the current configuration.
        
        Raises:
            ValidationError: If configuration is invalid.
        """
        # Validate primary color
        primary_color = self._config.get("primary_color")
        if primary_color and not is_valid_hex_color(primary_color):
            raise ValidationError(
                user_message=f"Invalid primary_color format: '{primary_color}'",
                internal_error=None
            )
        
        # Validate margins are non-negative
        for margin_name in ["margin_top", "margin_bottom", "margin_left", "margin_right"]:
            value = self._config.get(margin_name, 0)
            if value < 0:
                raise ValidationError(
                    user_message=f"{margin_name} cannot be negative, got {value}",
                    internal_error=None
                )
        
        # Validate heights are non-negative
        for height_name in ["header_height", "footer_height"]:
            value = self._config.get(height_name, 0)
            if value < 0:
                raise ValidationError(
                    user_message=f"{height_name} cannot be negative, got {value}",
                    internal_error=None
                )
    
    @property
    def config(self) -> dict[str, Any]:
        """Get the current configuration dictionary."""
        return dict(self._config)
    
    @property
    def charts(self) -> list["ChartConfig"]:
        """Get the configured charts."""
        return list(self._charts)
