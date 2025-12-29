"""
Asset management for qry-doc.

This module provides the AssetManager class for managing package assets
like the default logo and validating user-provided asset paths.
"""
import logging
from importlib import resources
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Supported image formats
SUPPORTED_IMAGE_FORMATS = {".png", ".jpg", ".jpeg"}
# Supported font formats
SUPPORTED_FONT_FORMATS = {".ttf", ".otf"}


class AssetManager:
    """
    Manages package assets like default logo and validates asset paths.
    
    This class provides methods to:
    - Get the path to the default logo bundled with the package
    - Validate image paths (existence and format)
    - Validate font paths (existence and format)
    """
    
    ASSETS_PACKAGE = "qry_doc.assets"
    DEFAULT_LOGO_FILENAME = "default_logo.png"
    
    @classmethod
    def get_default_logo_path(cls) -> Optional[Path]:
        """
        Get the path to the default logo using importlib.resources.
        
        Returns:
            Path to the default logo, or None if not found.
        """
        try:
            # Python 3.9+ approach using files()
            files = resources.files(cls.ASSETS_PACKAGE)
            logo_resource = files.joinpath(cls.DEFAULT_LOGO_FILENAME)
            
            # Check if the resource exists
            if logo_resource.is_file():
                # For actual file access, we need to use as_file context
                # But for path checking, we can return the traversable path
                with resources.as_file(logo_resource) as path:
                    if path.exists():
                        return path
            return None
        except (ModuleNotFoundError, FileNotFoundError, TypeError) as e:
            logger.warning(f"Default logo not found in package assets: {e}")
            return None
    
    @classmethod
    def validate_image_path(cls, path: Optional[Path]) -> tuple[bool, str]:
        """
        Validate that an image path exists and has a supported format.
        
        Args:
            path: Path to the image file.
            
        Returns:
            Tuple of (is_valid, error_message).
            If valid, error_message is empty string.
        """
        if path is None:
            return False, "Image path is None"
        
        # Convert to Path if string
        if isinstance(path, str):
            path = Path(path)
        
        # Check existence
        if not path.exists():
            return False, f"Image not found: {path}"
        
        # Check format
        suffix = path.suffix.lower()
        if suffix not in SUPPORTED_IMAGE_FORMATS:
            return False, (
                f"Invalid image format: {suffix}. "
                f"Supported: {', '.join(SUPPORTED_IMAGE_FORMATS)}"
            )
        
        return True, ""
    
    @classmethod
    def validate_font_path(cls, path: Optional[Path]) -> tuple[bool, str]:
        """
        Validate that a font path exists and has a supported format.
        
        Args:
            path: Path to the font file.
            
        Returns:
            Tuple of (is_valid, error_message).
            If valid, error_message is empty string.
        """
        if path is None:
            return False, "Font path is None"
        
        # Convert to Path if string
        if isinstance(path, str):
            path = Path(path)
        
        # Check existence
        if not path.exists():
            return False, f"Font file not found: {path}"
        
        # Check format
        suffix = path.suffix.lower()
        if suffix not in SUPPORTED_FONT_FORMATS:
            return False, (
                f"Invalid font format: {suffix}. "
                f"Supported: {', '.join(SUPPORTED_FONT_FORMATS)}"
            )
        
        return True, ""
