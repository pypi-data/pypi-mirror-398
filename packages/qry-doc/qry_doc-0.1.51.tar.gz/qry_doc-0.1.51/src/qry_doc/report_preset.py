"""
Report presets for industry-specific PDF reports.

This module provides ReportPreset and ReportPresetType for creating
professional reports tailored to different industries.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any

from reportlab.lib.pagesizes import letter

from qry_doc.report_template import ReportTemplate, SectionType, SectionConfig
from qry_doc.exceptions import ValidationError


class ReportPresetType(Enum):
    """
    Types of industry-specific report presets.
    
    Attributes:
        FINANCIAL: Financial and banking reports with blue tones.
        HEALTHCARE: Healthcare and medical reports with green/teal tones.
        TECHNOLOGY: Technology and software reports with modern purple tones.
        RETAIL: Retail and e-commerce reports with orange/warm tones.
        MANUFACTURING: Manufacturing and industrial reports with gray/steel tones.
        CONSULTING: Consulting and professional services with navy/gold tones.
    """
    FINANCIAL = "financial"
    HEALTHCARE = "healthcare"
    TECHNOLOGY = "technology"
    RETAIL = "retail"
    MANUFACTURING = "manufacturing"
    CONSULTING = "consulting"


@dataclass
class ReportPreset:
    """
    Industry-specific report preset configuration.
    
    Provides predefined color schemes, fonts, and section layouts
    optimized for different industries.
    
    Attributes:
        preset_type: The industry type for this preset.
        name: Human-readable name of the preset.
        description: Description of the preset's intended use.
        primary_color: Primary hex color for headings and accents.
        secondary_color: Secondary hex color for highlights.
        title_font: Font family for titles.
        body_font: Font family for body text.
        default_sections: List of default section configurations.
    
    Example:
        ```python
        preset = ReportPreset.get(ReportPresetType.FINANCIAL)
        template = preset.to_template()
        
        # Or with overrides
        template = preset.to_template(primary_color="#001122")
        ```
    """
    preset_type: ReportPresetType
    name: str
    description: str
    primary_color: str
    secondary_color: str
    title_font: str
    body_font: str
    default_sections: list[SectionConfig] = field(default_factory=list)
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate that all required fields are provided.
        
        Returns:
            Tuple of (is_valid, error_message).
        """
        required_fields = [
            ("preset_type", self.preset_type),
            ("name", self.name),
            ("primary_color", self.primary_color),
            ("title_font", self.title_font),
            ("body_font", self.body_font),
            ("default_sections", self.default_sections),
        ]
        
        for field_name, value in required_fields:
            if value is None:
                return False, f"Missing required field: {field_name}"
            if field_name == "default_sections" and len(value) == 0:
                return False, f"default_sections cannot be empty"
        
        return True, None
    
    def to_template(self, **overrides: Any) -> ReportTemplate:
        """
        Convert the preset to a ReportTemplate with optional overrides.
        
        Args:
            **overrides: Keyword arguments to override preset values.
                        Supported: primary_color, title_font, body_font,
                        page_size, margin_top, margin_bottom, margin_left,
                        margin_right, header_height, footer_height, sections.
        
        Returns:
            ReportTemplate configured with preset values and overrides.
            
        Example:
            ```python
            preset = ReportPreset.get(ReportPresetType.FINANCIAL)
            
            # Use preset as-is
            template = preset.to_template()
            
            # Override specific values
            template = preset.to_template(
                primary_color="#001122",
                margin_top=100.0
            )
            ```
        """
        # Start with preset values
        config = {
            "primary_color": self.primary_color,
            "title_font": self.title_font,
            "body_font": self.body_font,
            "sections": list(self.default_sections),
        }
        
        # Apply overrides
        for key, value in overrides.items():
            if key in config or hasattr(ReportTemplate, key):
                config[key] = value
        
        return ReportTemplate(**config)
    
    @classmethod
    def get(cls, preset_type: ReportPresetType) -> "ReportPreset":
        """
        Get a preset by type.
        
        Args:
            preset_type: The type of preset to retrieve.
            
        Returns:
            ReportPreset for the specified type.
            
        Raises:
            ValueError: If preset_type is not recognized.
        """
        presets = cls._get_all_presets()
        
        if preset_type not in presets:
            raise ValueError(f"Unknown preset type: {preset_type}")
        
        return presets[preset_type]
    
    @classmethod
    def list_all(cls) -> list[tuple[str, str]]:
        """
        List all available presets with their descriptions.
        
        Returns:
            List of (name, description) tuples for all presets.
            
        Example:
            ```python
            for name, description in ReportPreset.list_all():
                print(f"{name}: {description}")
            ```
        """
        presets = cls._get_all_presets()
        return [(p.name, p.description) for p in presets.values()]
    
    @classmethod
    def _get_all_presets(cls) -> dict[ReportPresetType, "ReportPreset"]:
        """Get all predefined presets."""
        return {
            ReportPresetType.FINANCIAL: cls._financial_preset(),
            ReportPresetType.HEALTHCARE: cls._healthcare_preset(),
            ReportPresetType.TECHNOLOGY: cls._technology_preset(),
            ReportPresetType.RETAIL: cls._retail_preset(),
            ReportPresetType.MANUFACTURING: cls._manufacturing_preset(),
            ReportPresetType.CONSULTING: cls._consulting_preset(),
        }
    
    @classmethod
    def _financial_preset(cls) -> "ReportPreset":
        """Create the financial industry preset."""
        return cls(
            preset_type=ReportPresetType.FINANCIAL,
            name="Financial",
            description="Professional financial reports with blue tones, ideal for banking, investment, and accounting.",
            primary_color="#003366",
            secondary_color="#0066CC",
            title_font="Helvetica-Bold",
            body_font="Helvetica",
            default_sections=[
                SectionConfig(SectionType.COVER),
                SectionConfig(SectionType.SUMMARY),
                SectionConfig(SectionType.CHART),
                SectionConfig(SectionType.DATA),
            ],
        )
    
    @classmethod
    def _healthcare_preset(cls) -> "ReportPreset":
        """Create the healthcare industry preset."""
        return cls(
            preset_type=ReportPresetType.HEALTHCARE,
            name="Healthcare",
            description="Clean healthcare reports with green/teal tones, ideal for medical, pharmaceutical, and wellness.",
            primary_color="#006666",
            secondary_color="#00A3A3",
            title_font="Helvetica-Bold",
            body_font="Helvetica",
            default_sections=[
                SectionConfig(SectionType.COVER),
                SectionConfig(SectionType.SUMMARY),
                SectionConfig(SectionType.DATA),
                SectionConfig(SectionType.CHART),
            ],
        )
    
    @classmethod
    def _technology_preset(cls) -> "ReportPreset":
        """Create the technology industry preset."""
        return cls(
            preset_type=ReportPresetType.TECHNOLOGY,
            name="Technology",
            description="Modern technology reports with purple tones, ideal for software, IT, and digital services.",
            primary_color="#5C2D91",
            secondary_color="#8661C5",
            title_font="Helvetica-Bold",
            body_font="Helvetica",
            default_sections=[
                SectionConfig(SectionType.SUMMARY),
                SectionConfig(SectionType.CHART),
                SectionConfig(SectionType.CHART),
                SectionConfig(SectionType.DATA),
            ],
        )
    
    @classmethod
    def _retail_preset(cls) -> "ReportPreset":
        """Create the retail industry preset."""
        return cls(
            preset_type=ReportPresetType.RETAIL,
            name="Retail",
            description="Vibrant retail reports with orange/warm tones, ideal for e-commerce, sales, and consumer goods.",
            primary_color="#E65100",
            secondary_color="#FF9800",
            title_font="Helvetica-Bold",
            body_font="Helvetica",
            default_sections=[
                SectionConfig(SectionType.COVER),
                SectionConfig(SectionType.SUMMARY),
                SectionConfig(SectionType.CHART),
                SectionConfig(SectionType.DATA),
            ],
        )
    
    @classmethod
    def _manufacturing_preset(cls) -> "ReportPreset":
        """Create the manufacturing industry preset."""
        return cls(
            preset_type=ReportPresetType.MANUFACTURING,
            name="Manufacturing",
            description="Industrial manufacturing reports with gray/steel tones, ideal for production, logistics, and engineering.",
            primary_color="#455A64",
            secondary_color="#78909C",
            title_font="Helvetica-Bold",
            body_font="Helvetica",
            default_sections=[
                SectionConfig(SectionType.SUMMARY),
                SectionConfig(SectionType.DATA),
                SectionConfig(SectionType.CHART),
                SectionConfig(SectionType.DATA),
            ],
        )
    
    @classmethod
    def _consulting_preset(cls) -> "ReportPreset":
        """Create the consulting industry preset."""
        return cls(
            preset_type=ReportPresetType.CONSULTING,
            name="Consulting",
            description="Executive consulting reports with navy/gold tones, ideal for strategy, management, and professional services.",
            primary_color="#1A237E",
            secondary_color="#C9A227",
            title_font="Helvetica-Bold",
            body_font="Helvetica",
            default_sections=[
                SectionConfig(SectionType.COVER),
                SectionConfig(SectionType.SUMMARY),
                SectionConfig(SectionType.CHART),
                SectionConfig(SectionType.DATA),
                SectionConfig(SectionType.CUSTOM, custom_content=""),
            ],
        )


def list_presets() -> list[tuple[str, str]]:
    """
    List all available report presets.
    
    Convenience function that wraps ReportPreset.list_all().
    
    Returns:
        List of (name, description) tuples for all presets.
        
    Example:
        ```python
        from qry_doc import list_presets
        
        for name, description in list_presets():
            print(f"{name}: {description}")
        ```
    """
    return ReportPreset.list_all()
