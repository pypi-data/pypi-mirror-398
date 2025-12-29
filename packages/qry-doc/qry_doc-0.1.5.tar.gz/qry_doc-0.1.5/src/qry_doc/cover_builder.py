"""
Cover builder for dynamic PDF cover pages.

This module provides CoverBuilder for constructing dynamic cover pages
with configurable text elements, background images, and colors.
"""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

from reportlab.lib.pagesizes import letter

from qry_doc.text_element import TextElement, TextAlignment, is_valid_hex_color
from qry_doc.exceptions import ValidationError


# Type alias for page size tuples
PageSize = tuple[float, float]


@dataclass
class CoverConfig:
    """
    Complete configuration for a cover page.
    
    Attributes:
        elements: List of TextElement objects to render.
        background_image: Optional path to background image.
        background_color: Optional hex color for background.
        background_opacity: Opacity for background image (0.0 to 1.0).
        page_size: Page dimensions as (width, height) tuple.
    """
    elements: list[TextElement] = field(default_factory=list)
    background_image: Optional[Path] = None
    background_color: Optional[str] = None
    background_opacity: float = 1.0
    page_size: PageSize = field(default_factory=lambda: letter)


class CoverBuilder:
    """
    Fluent builder for constructing dynamic PDF cover pages.
    
    Provides a chainable API for configuring cover page elements
    including title, subtitle, date, author, and background.
    
    Example:
        ```python
        cover = (
            CoverBuilder()
            .set_title("Annual Report 2024", font_size=48, color="#003366")
            .set_subtitle("Financial Analysis", font_size=24)
            .set_date(datetime.now())
            .set_author("John Doe")
            .set_background_color("#F5F5F5")
            .build()
        )
        ```
    """
    
    # Default positions for elements (in points from bottom-left)
    # Based on letter size (612 x 792 points)
    DEFAULT_POSITIONS = {
        "title": {"x": 306.0, "y": 500.0},      # Centered horizontally, upper third
        "subtitle": {"x": 306.0, "y": 450.0},   # Below title
        "date": {"x": 306.0, "y": 150.0},       # Lower area
        "author": {"x": 306.0, "y": 120.0},     # Below date
    }
    
    # Default styles for elements
    DEFAULT_STYLES = {
        "title": {
            "font_size": 36.0,
            "font_family": "Helvetica-Bold",
            "color": "#000000",
            "alignment": TextAlignment.CENTER,
        },
        "subtitle": {
            "font_size": 24.0,
            "font_family": "Helvetica",
            "color": "#333333",
            "alignment": TextAlignment.CENTER,
        },
        "date": {
            "font_size": 14.0,
            "font_family": "Helvetica",
            "color": "#666666",
            "alignment": TextAlignment.CENTER,
        },
        "author": {
            "font_size": 14.0,
            "font_family": "Helvetica",
            "color": "#666666",
            "alignment": TextAlignment.CENTER,
        },
    }
    
    def __init__(self, page_size: PageSize = letter) -> None:
        """
        Initialize the CoverBuilder.
        
        Args:
            page_size: Page dimensions as (width, height) tuple.
                      Default is letter size (612 x 792 points).
        """
        self._page_size = page_size
        self._elements: list[TextElement] = []
        self._background_image: Optional[Path] = None
        self._background_color: Optional[str] = None
        self._background_opacity: float = 1.0
    
    def _get_default_position(self, element_type: str) -> tuple[float, float]:
        """Get default position for an element type."""
        defaults = self.DEFAULT_POSITIONS.get(element_type, {"x": 306.0, "y": 400.0})
        return defaults["x"], defaults["y"]
    
    def _get_default_style(self, element_type: str) -> dict:
        """Get default style for an element type."""
        return self.DEFAULT_STYLES.get(element_type, {
            "font_size": 12.0,
            "font_family": "Helvetica",
            "color": "#000000",
            "alignment": TextAlignment.LEFT,
        })
    
    def _validate_color(self, color: str) -> None:
        """Validate hex color format."""
        if not is_valid_hex_color(color):
            raise ValidationError(
                user_message=f"Invalid hex color format: '{color}'. Use format like '#FF0000'.",
                internal_error=None
            )
    
    def _validate_font_size(self, font_size: float) -> None:
        """Validate font size is positive."""
        if font_size <= 0:
            raise ValidationError(
                user_message=f"font_size must be positive, got {font_size}",
                internal_error=None
            )
    
    def set_title(
        self,
        text: str,
        font_size: Optional[float] = None,
        x: Optional[float] = None,
        y: Optional[float] = None,
        color: Optional[str] = None,
        font_family: Optional[str] = None,
        alignment: Optional[TextAlignment] = None,
    ) -> "CoverBuilder":
        """
        Configure the title element.
        
        Args:
            text: Title text content.
            font_size: Font size in points. Default 36.0.
            x: X position in points. Default centered.
            y: Y position in points. Default upper third.
            color: Hex color code. Default "#000000".
            font_family: Font family name. Default "Helvetica-Bold".
            alignment: Text alignment. Default CENTER.
            
        Returns:
            Self for method chaining.
            
        Raises:
            ValidationError: If font_size is not positive or color is invalid.
        """
        defaults = self._get_default_style("title")
        default_x, default_y = self._get_default_position("title")
        
        final_font_size = font_size if font_size is not None else defaults["font_size"]
        final_color = color if color is not None else defaults["color"]
        
        self._validate_font_size(final_font_size)
        self._validate_color(final_color)
        
        element = TextElement(
            content=text,
            x=x if x is not None else default_x,
            y=y if y is not None else default_y,
            font_size=final_font_size,
            font_family=font_family if font_family is not None else defaults["font_family"],
            color=final_color,
            alignment=alignment if alignment is not None else defaults["alignment"],
            element_type="title",
        )
        
        # Remove existing title if any
        self._elements = [e for e in self._elements if e.element_type != "title"]
        self._elements.append(element)
        
        return self
    
    def set_subtitle(
        self,
        text: str,
        font_size: Optional[float] = None,
        x: Optional[float] = None,
        y: Optional[float] = None,
        color: Optional[str] = None,
        font_family: Optional[str] = None,
        alignment: Optional[TextAlignment] = None,
    ) -> "CoverBuilder":
        """
        Configure the subtitle element.
        
        Args:
            text: Subtitle text content.
            font_size: Font size in points. Default 24.0.
            x: X position in points. Default centered.
            y: Y position in points. Default below title.
            color: Hex color code. Default "#333333".
            font_family: Font family name. Default "Helvetica".
            alignment: Text alignment. Default CENTER.
            
        Returns:
            Self for method chaining.
            
        Raises:
            ValidationError: If font_size is not positive or color is invalid.
        """
        defaults = self._get_default_style("subtitle")
        default_x, default_y = self._get_default_position("subtitle")
        
        final_font_size = font_size if font_size is not None else defaults["font_size"]
        final_color = color if color is not None else defaults["color"]
        
        self._validate_font_size(final_font_size)
        self._validate_color(final_color)
        
        element = TextElement(
            content=text,
            x=x if x is not None else default_x,
            y=y if y is not None else default_y,
            font_size=final_font_size,
            font_family=font_family if font_family is not None else defaults["font_family"],
            color=final_color,
            alignment=alignment if alignment is not None else defaults["alignment"],
            element_type="subtitle",
        )
        
        self._elements = [e for e in self._elements if e.element_type != "subtitle"]
        self._elements.append(element)
        
        return self
    
    def set_date(
        self,
        date: Union[str, datetime],
        format: str = "%B %d, %Y",
        x: Optional[float] = None,
        y: Optional[float] = None,
        font_size: Optional[float] = None,
        color: Optional[str] = None,
        font_family: Optional[str] = None,
        alignment: Optional[TextAlignment] = None,
    ) -> "CoverBuilder":
        """
        Configure the date element.
        
        Args:
            date: Date value (string or datetime object).
            format: Date format string for datetime objects. Default "%B %d, %Y".
            x: X position in points. Default centered.
            y: Y position in points. Default lower area.
            font_size: Font size in points. Default 14.0.
            color: Hex color code. Default "#666666".
            font_family: Font family name. Default "Helvetica".
            alignment: Text alignment. Default CENTER.
            
        Returns:
            Self for method chaining.
            
        Raises:
            ValidationError: If font_size is not positive or color is invalid.
        """
        defaults = self._get_default_style("date")
        default_x, default_y = self._get_default_position("date")
        
        # Format date if datetime object
        if isinstance(date, datetime):
            date_text = date.strftime(format)
        else:
            date_text = str(date)
        
        final_font_size = font_size if font_size is not None else defaults["font_size"]
        final_color = color if color is not None else defaults["color"]
        
        self._validate_font_size(final_font_size)
        self._validate_color(final_color)
        
        element = TextElement(
            content=date_text,
            x=x if x is not None else default_x,
            y=y if y is not None else default_y,
            font_size=final_font_size,
            font_family=font_family if font_family is not None else defaults["font_family"],
            color=final_color,
            alignment=alignment if alignment is not None else defaults["alignment"],
            element_type="date",
        )
        
        self._elements = [e for e in self._elements if e.element_type != "date"]
        self._elements.append(element)
        
        return self
    
    def set_author(
        self,
        name: str,
        x: Optional[float] = None,
        y: Optional[float] = None,
        font_size: Optional[float] = None,
        color: Optional[str] = None,
        font_family: Optional[str] = None,
        alignment: Optional[TextAlignment] = None,
    ) -> "CoverBuilder":
        """
        Configure the author element.
        
        Args:
            name: Author name.
            x: X position in points. Default centered.
            y: Y position in points. Default below date.
            font_size: Font size in points. Default 14.0.
            color: Hex color code. Default "#666666".
            font_family: Font family name. Default "Helvetica".
            alignment: Text alignment. Default CENTER.
            
        Returns:
            Self for method chaining.
            
        Raises:
            ValidationError: If font_size is not positive or color is invalid.
        """
        defaults = self._get_default_style("author")
        default_x, default_y = self._get_default_position("author")
        
        final_font_size = font_size if font_size is not None else defaults["font_size"]
        final_color = color if color is not None else defaults["color"]
        
        self._validate_font_size(final_font_size)
        self._validate_color(final_color)
        
        element = TextElement(
            content=name,
            x=x if x is not None else default_x,
            y=y if y is not None else default_y,
            font_size=final_font_size,
            font_family=font_family if font_family is not None else defaults["font_family"],
            color=final_color,
            alignment=alignment if alignment is not None else defaults["alignment"],
            element_type="author",
        )
        
        self._elements = [e for e in self._elements if e.element_type != "author"]
        self._elements.append(element)
        
        return self
    
    def add_custom_text(
        self,
        text: str,
        x: float,
        y: float,
        font_size: float = 12.0,
        color: str = "#000000",
        font_family: str = "Helvetica",
        alignment: TextAlignment = TextAlignment.LEFT,
    ) -> "CoverBuilder":
        """
        Add a custom text element at a specific position.
        
        Args:
            text: Text content.
            x: X position in points from bottom-left.
            y: Y position in points from bottom-left.
            font_size: Font size in points. Default 12.0.
            color: Hex color code. Default "#000000".
            font_family: Font family name. Default "Helvetica".
            alignment: Text alignment. Default LEFT.
            
        Returns:
            Self for method chaining.
            
        Raises:
            ValidationError: If font_size is not positive or color is invalid.
        """
        self._validate_font_size(font_size)
        self._validate_color(color)
        
        element = TextElement(
            content=text,
            x=x,
            y=y,
            font_size=font_size,
            font_family=font_family,
            color=color,
            alignment=alignment,
            element_type="custom",
        )
        
        self._elements.append(element)
        
        return self
    
    def set_background_image(
        self,
        path: Union[str, Path],
        opacity: float = 1.0,
    ) -> "CoverBuilder":
        """
        Configure background image.
        
        Args:
            path: Path to the background image file.
            opacity: Image opacity (0.0 to 1.0). Default 1.0.
            
        Returns:
            Self for method chaining.
            
        Raises:
            ValidationError: If opacity is out of range.
        """
        if not 0.0 <= opacity <= 1.0:
            raise ValidationError(
                user_message=f"opacity must be between 0.0 and 1.0, got {opacity}",
                internal_error=None
            )
        
        self._background_image = Path(path) if isinstance(path, str) else path
        self._background_opacity = opacity
        
        return self
    
    def set_background_color(self, color: str) -> "CoverBuilder":
        """
        Configure background color.
        
        Args:
            color: Hex color code (e.g., "#F5F5F5").
            
        Returns:
            Self for method chaining.
            
        Raises:
            ValidationError: If color is not a valid hex format.
        """
        self._validate_color(color)
        self._background_color = color.upper()
        
        return self
    
    def build(self) -> CoverConfig:
        """
        Build and return the cover configuration.
        
        Validates all elements and returns a CoverConfig object.
        
        Returns:
            CoverConfig with all configured elements and settings.
            
        Raises:
            ValidationError: If any element fails validation.
        """
        # Validate all elements
        for element in self._elements:
            is_valid, error = element.validate()
            if not is_valid:
                raise ValidationError(
                    user_message=f"Invalid element '{element.element_type}': {error}",
                    internal_error=None
                )
        
        return CoverConfig(
            elements=list(self._elements),
            background_image=self._background_image,
            background_color=self._background_color,
            background_opacity=self._background_opacity,
            page_size=self._page_size,
        )
    
    @property
    def elements(self) -> list[TextElement]:
        """Get the current list of elements."""
        return list(self._elements)
    
    @property
    def page_size(self) -> PageSize:
        """Get the configured page size."""
        return self._page_size
