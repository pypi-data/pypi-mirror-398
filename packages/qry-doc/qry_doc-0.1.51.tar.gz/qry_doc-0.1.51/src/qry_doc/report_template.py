"""
Report template configuration for qry-doc.

This module provides the ReportTemplate class for customizing
the appearance of generated PDF reports.
"""
import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Optional, Callable

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.colors import HexColor, Color
from reportlab.lib.units import inch

from qry_doc.asset_manager import AssetManager

logger = logging.getLogger(__name__)


# Type alias for page size tuples
PageSize = tuple[float, float]


class SectionType(Enum):
    """
    Types of sections available in a PDF report.
    
    Attributes:
        COVER: Cover page with full-page image.
        SUMMARY: Executive summary text section.
        DATA: DataFrame rendered as a table.
        CHART: Chart/visualization image.
        CUSTOM: User-provided arbitrary content.
    """
    COVER = auto()
    SUMMARY = auto()
    DATA = auto()
    CHART = auto()
    CUSTOM = auto()


class LogoPosition(Enum):
    """
    Positions for the footer logo in PDF reports.
    
    Attributes:
        BOTTOM_RIGHT: Logo in bottom-right corner (default).
        BOTTOM_LEFT: Logo in bottom-left corner.
        BOTTOM_CENTER: Logo centered at bottom.
    """
    BOTTOM_RIGHT = "bottom_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"


@dataclass
class SectionConfig:
    """
    Configuration for a report section.
    
    Attributes:
        section_type: Type of section (COVER, SUMMARY, DATA, CHART, CUSTOM).
        enabled: Whether this section should be rendered.
        custom_content: Content for CUSTOM sections (ignored for other types).
    """
    section_type: SectionType
    enabled: bool = True
    custom_content: Optional[str] = None


@dataclass
class ReportTemplate:
    """
    Configuration for PDF report styling.
    
    Attributes:
        logo_path: Path to logo image file for header (PNG, JPG).
        primary_color: Hex color for headings and accents (e.g., "#1a1a2e").
        title_font: Font family for titles (e.g., "Helvetica-Bold").
        body_font: Font family for body text (e.g., "Helvetica").
        page_size: Page dimensions as (width, height) tuple.
        margin_top: Top margin in points.
        margin_bottom: Bottom margin in points.
        margin_left: Left margin in points.
        margin_right: Right margin in points.
        header_height: Height reserved for header in points.
        footer_height: Height reserved for footer in points.
        cover_image_path: Path to cover page image (full page).
        footer_logo_path: Path to footer logo (None = use default).
        footer_logo_enabled: Whether to show footer logo.
        footer_logo_position: Position of footer logo.
        footer_logo_width: Width of footer logo in points.
        footer_logo_height: Height of footer logo in points.
        custom_title_font_path: Path to custom TTF/OTF font for titles.
        custom_body_font_path: Path to custom TTF/OTF font for body.
        sections: List of section configurations for report structure.
    """
    
    # Header logo (existing)
    logo_path: Optional[Path] = None
    
    # Colors and fonts
    primary_color: str = "#1a1a2e"
    title_font: str = "Helvetica-Bold"
    body_font: str = "Helvetica"
    
    # Page layout
    page_size: PageSize = field(default_factory=lambda: letter)
    margin_top: float = 72.0  # 1 inch
    margin_bottom: float = 72.0
    margin_left: float = 72.0
    margin_right: float = 72.0
    header_height: float = 50.0
    footer_height: float = 30.0
    
    # Cover page (new)
    cover_image_path: Optional[Path] = None
    
    # Footer logo (new)
    footer_logo_path: Optional[Path] = None  # None = use default
    footer_logo_enabled: bool = True
    footer_logo_position: LogoPosition = LogoPosition.BOTTOM_RIGHT
    footer_logo_width: float = 120.0  # points
    footer_logo_height: float = 60.0  # points
    
    # Custom fonts (new)
    custom_title_font_path: Optional[Path] = None
    custom_body_font_path: Optional[Path] = None
    
    # Sections (new)
    sections: list[SectionConfig] = field(default_factory=list)
    
    # Callbacks for custom header/footer (set after initialization)
    _header_callback: Optional[Callable[[Any, Any], None]] = field(
        default=None, repr=False
    )
    _footer_callback: Optional[Callable[[Any, Any], None]] = field(
        default=None, repr=False
    )
    
    def __post_init__(self) -> None:
        """Validate and convert fields after initialization."""
        # Convert string paths to Path objects
        if isinstance(self.logo_path, str):
            self.logo_path = Path(self.logo_path)
        if isinstance(self.cover_image_path, str):
            self.cover_image_path = Path(self.cover_image_path)
        if isinstance(self.footer_logo_path, str):
            self.footer_logo_path = Path(self.footer_logo_path)
        if isinstance(self.custom_title_font_path, str):
            self.custom_title_font_path = Path(self.custom_title_font_path)
        if isinstance(self.custom_body_font_path, str):
            self.custom_body_font_path = Path(self.custom_body_font_path)
        
        # Validate color format
        if not self.primary_color.startswith("#"):
            self.primary_color = f"#{self.primary_color}"
    
    @property
    def primary_color_obj(self) -> Color:
        """Get the primary color as a ReportLab Color object."""
        return HexColor(self.primary_color)
    
    @property
    def page_width(self) -> float:
        """Get the page width in points."""
        return self.page_size[0]
    
    @property
    def page_height(self) -> float:
        """Get the page height in points."""
        return self.page_size[1]
    
    @property
    def content_width(self) -> float:
        """Get the available content width (page width minus margins)."""
        return self.page_width - self.margin_left - self.margin_right
    
    @property
    def content_height(self) -> float:
        """Get the available content height (page height minus margins and header/footer)."""
        return (
            self.page_height 
            - self.margin_top 
            - self.margin_bottom 
            - self.header_height 
            - self.footer_height
        )
    
    def get_footer_logo_path(self) -> Optional[Path]:
        """
        Get the path to the footer logo.
        
        Returns the custom footer logo path if set, otherwise returns the
        default logo from the package assets. Returns None if footer logo
        is disabled.
        
        Returns:
            Path to footer logo, or None if disabled or not available.
        """
        if not self.footer_logo_enabled:
            return None
        
        # Use custom path if provided
        if self.footer_logo_path is not None:
            return self.footer_logo_path
        
        # Fall back to default logo
        return AssetManager.get_default_logo_path()
    
    def _calculate_footer_logo_position(self) -> tuple[float, float]:
        """
        Calculate the x, y position for the footer logo based on configuration.
        
        Returns:
            Tuple of (x, y) coordinates in points.
        """
        y = self.margin_bottom - self.footer_logo_height - 5
        
        if self.footer_logo_position == LogoPosition.BOTTOM_RIGHT:
            x = self.page_width - self.margin_right - self.footer_logo_width
        elif self.footer_logo_position == LogoPosition.BOTTOM_LEFT:
            x = self.margin_left
        else:  # BOTTOM_CENTER
            x = (self.page_width - self.footer_logo_width) / 2
        
        return x, y
    
    def register_custom_fonts(self) -> tuple[str, str]:
        """
        Register custom fonts if provided and return the font names to use.
        
        Validates font paths and registers TTF/OTF fonts with ReportLab.
        Falls back to default Helvetica fonts if registration fails.
        
        Returns:
            Tuple of (title_font_name, body_font_name) to use in styles.
        """
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        
        title_font = self.title_font
        body_font = self.body_font
        
        # Register custom title font
        if self.custom_title_font_path is not None:
            is_valid, error_msg = AssetManager.validate_font_path(
                self.custom_title_font_path
            )
            if is_valid:
                try:
                    font_name = f"CustomTitle-{self.custom_title_font_path.stem}"
                    pdfmetrics.registerFont(
                        TTFont(font_name, str(self.custom_title_font_path))
                    )
                    title_font = font_name
                    logger.info(f"Registered custom title font: {font_name}")
                except Exception as e:
                    logger.warning(
                        f"Failed to register font {self.custom_title_font_path}: {e}. "
                        "Using default font."
                    )
            else:
                logger.warning(f"{error_msg}. Using default font.")
        
        # Register custom body font
        if self.custom_body_font_path is not None:
            is_valid, error_msg = AssetManager.validate_font_path(
                self.custom_body_font_path
            )
            if is_valid:
                try:
                    font_name = f"CustomBody-{self.custom_body_font_path.stem}"
                    pdfmetrics.registerFont(
                        TTFont(font_name, str(self.custom_body_font_path))
                    )
                    body_font = font_name
                    logger.info(f"Registered custom body font: {font_name}")
                except Exception as e:
                    logger.warning(
                        f"Failed to register font {self.custom_body_font_path}: {e}. "
                        "Using default font."
                    )
            else:
                logger.warning(f"{error_msg}. Using default font.")
        
        return title_font, body_font
    
    def draw_header(self, canvas: Any, doc: Any) -> None:
        """
        Draw the header on the current page.
        
        Override this method or set _header_callback for custom headers.
        
        Args:
            canvas: ReportLab canvas object.
            doc: ReportLab document object.
        """
        if self._header_callback is not None:
            self._header_callback(canvas, doc)
            return
        
        # Default header implementation
        canvas.saveState()
        
        # Draw logo if provided
        if self.logo_path and self.logo_path.exists():
            try:
                canvas.drawImage(
                    str(self.logo_path),
                    self.margin_left,
                    self.page_height - self.margin_top - 40,
                    width=100,
                    height=40,
                    preserveAspectRatio=True,
                    mask='auto'
                )
            except Exception:
                pass  # Skip logo if it can't be loaded
        
        # Draw a line under the header
        canvas.setStrokeColor(self.primary_color_obj)
        canvas.setLineWidth(1)
        y_pos = self.page_height - self.margin_top - self.header_height
        canvas.line(
            self.margin_left,
            y_pos,
            self.page_width - self.margin_right,
            y_pos
        )
        
        canvas.restoreState()
    
    def draw_footer(self, canvas: Any, doc: Any) -> None:
        """
        Draw the footer on the current page.
        
        Override this method or set _footer_callback for custom footers.
        
        Args:
            canvas: ReportLab canvas object.
            doc: ReportLab document object.
        """
        if self._footer_callback is not None:
            self._footer_callback(canvas, doc)
            return
        
        # Default footer implementation
        canvas.saveState()
        
        # Draw page number
        page_num = doc.page
        canvas.setFont(self.body_font, 9)
        canvas.setFillColor(HexColor("#666666"))
        
        text = f"Página {page_num}"
        canvas.drawCentredString(
            self.page_width / 2,
            self.margin_bottom - 20,
            text
        )
        
        # Draw footer logo if enabled
        logo_path = self.get_footer_logo_path()
        if logo_path is not None:
            if logo_path.exists():
                try:
                    x, y = self._calculate_footer_logo_position()
                    canvas.drawImage(
                        str(logo_path),
                        x,
                        y,
                        width=self.footer_logo_width,
                        height=self.footer_logo_height,
                        preserveAspectRatio=True,
                        mask='auto'
                    )
                except Exception as e:
                    logger.warning(f"Failed to draw footer logo: {e}")
            else:
                logger.warning(f"Footer logo not found: {logo_path}. Skipping logo.")
        
        # Draw a line above the footer
        canvas.setStrokeColor(HexColor("#cccccc"))
        canvas.setLineWidth(0.5)
        y_pos = self.margin_bottom
        canvas.line(
            self.margin_left,
            y_pos,
            self.page_width - self.margin_right,
            y_pos
        )
        
        canvas.restoreState()
    
    def set_header_callback(self, callback: Callable[[Any, Any], None]) -> None:
        """
        Set a custom header drawing callback.
        
        Args:
            callback: Function that takes (canvas, doc) and draws the header.
        """
        self._header_callback = callback
    
    def set_footer_callback(self, callback: Callable[[Any, Any], None]) -> None:
        """
        Set a custom footer drawing callback.
        
        Args:
            callback: Function that takes (canvas, doc) and draws the footer.
        """
        self._footer_callback = callback


# Pre-defined templates
DEFAULT_TEMPLATE = ReportTemplate()

CORPORATE_TEMPLATE = ReportTemplate(
    primary_color="#003366",
    title_font="Helvetica-Bold",
    body_font="Helvetica",
    page_size=letter,
)

MINIMAL_TEMPLATE = ReportTemplate(
    primary_color="#333333",
    title_font="Helvetica",
    body_font="Helvetica",
    header_height=20.0,
    footer_height=20.0,
)

A4_TEMPLATE = ReportTemplate(
    page_size=A4,
)
