"""
Text element components for dynamic cover pages.

This module provides TextElement and TextAlignment for configuring
text elements on PDF cover pages with full control over position,
size, color, and font.
"""
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TextAlignment(Enum):
    """
    Text alignment options for TextElement.
    
    Attributes:
        LEFT: Align text to the left.
        CENTER: Center the text.
        RIGHT: Align text to the right.
    """
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


# Regex pattern for validating hex color codes
HEX_COLOR_PATTERN = re.compile(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$')


def is_valid_hex_color(color: str) -> bool:
    """
    Validate if a string is a valid hex color code.
    
    Args:
        color: String to validate (e.g., "#FF0000" or "#F00").
        
    Returns:
        True if valid hex color, False otherwise.
    """
    return bool(HEX_COLOR_PATTERN.match(color))


@dataclass
class TextElement:
    """
    Configurable text element for PDF cover pages.
    
    Represents a text element with full control over content, position,
    size, font, color, and alignment. Used by CoverBuilder to construct
    dynamic cover pages.
    
    Attributes:
        content: The text content to display.
        x: X position in points from bottom-left corner. Default 0.0.
        y: Y position in points from bottom-left corner. Default 0.0.
        font_size: Font size in points. Must be positive. Default 12.0.
        font_family: Font family name. Default "Helvetica".
        color: Hex color code (e.g., "#000000"). Default black.
        alignment: Text alignment. Default LEFT.
        element_type: Type identifier (title, subtitle, date, author, custom).
    
    Example:
        ```python
        title = TextElement(
            content="Annual Report 2024",
            x=72.0,
            y=700.0,
            font_size=36.0,
            font_family="Helvetica-Bold",
            color="#003366",
            alignment=TextAlignment.CENTER
        )
        ```
    """
    content: str
    x: float = 0.0
    y: float = 0.0
    font_size: float = 12.0
    font_family: str = "Helvetica"
    color: str = "#000000"
    alignment: TextAlignment = TextAlignment.LEFT
    element_type: str = "custom"
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate the text element parameters.
        
        Checks that:
        - font_size is a positive number
        - color is a valid hex format
        
        Returns:
            Tuple of (is_valid, error_message).
            If valid, returns (True, None).
            If invalid, returns (False, "error description").
            
        Example:
            ```python
            element = TextElement(content="Test", font_size=-5)
            is_valid, error = element.validate()
            # is_valid = False
            # error = "font_size must be a positive number, got -5"
            ```
        """
        # Validate font_size is positive
        if not isinstance(self.font_size, (int, float)):
            return False, f"font_size must be a number, got {type(self.font_size).__name__}"
        
        if self.font_size <= 0:
            return False, f"font_size must be a positive number, got {self.font_size}"
        
        # Validate color is valid hex format
        if not isinstance(self.color, str):
            return False, f"color must be a string, got {type(self.color).__name__}"
        
        if not is_valid_hex_color(self.color):
            return False, f"color must be a valid hex format (e.g., '#FF0000'), got '{self.color}'"
        
        return True, None
    
    def __post_init__(self) -> None:
        """
        Post-initialization processing.
        
        Normalizes the color to uppercase hex format if valid.
        """
        # Normalize color to uppercase if it's a valid hex
        if isinstance(self.color, str) and is_valid_hex_color(self.color):
            self.color = self.color.upper()
