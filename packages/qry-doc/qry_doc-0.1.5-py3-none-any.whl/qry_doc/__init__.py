"""
qry-doc: Motor de análisis generativo para consultas en lenguaje natural.

qry-doc transforma el lenguaje natural en código ejecutable, visualizaciones
y reportes PDF profesionales. Simplifica radicalmente la interacción con
archivos CSV y bases de datos SQL.

Example:
    ```python
    from qry_doc import QryDoc, ReportTemplate, SectionType, SectionConfig, LogoPosition
    from pandasai.llm import OpenAI
    
    # Inicializar con datos y LLM
    llm = OpenAI(api_token="your-api-key")
    qry = QryDoc("ventas.csv", llm=llm)
    
    # Hacer preguntas en lenguaje natural
    respuesta = qry.ask("¿Cuál fue el total de ventas en 2023?")
    print(respuesta)
    
    # Exportar resultados a CSV
    qry.extract_to_csv("Top 10 clientes por ventas", "top_clientes.csv")
    
    # Generar reporte PDF con portada y secciones personalizadas
    template = ReportTemplate(
        logo_path="logo.png",
        primary_color="#003366",
        cover_image_path="portada.png",
        footer_logo_position=LogoPosition.BOTTOM_RIGHT,
        sections=[
            SectionConfig(SectionType.SUMMARY),
            SectionConfig(SectionType.CHART),
            SectionConfig(SectionType.DATA),
        ]
    )
    qry.generate_report(
        "Análisis de tendencias de ventas",
        "reporte_ventas.pdf",
        template=template
    )
    ```
"""
from importlib import metadata

# Version from package metadata
try:
    __version__ = metadata.version("qry-doc")
except metadata.PackageNotFoundError:
    __version__ = "0.1.0"

# Main entry point
from qry_doc.core import QryDoc

# Templates and configuration
from qry_doc.report_template import (
    ReportTemplate,
    SectionType,
    SectionConfig,
    LogoPosition,
    DEFAULT_TEMPLATE,
    CORPORATE_TEMPLATE,
    MINIMAL_TEMPLATE,
    A4_TEMPLATE,
)

# New builder components
from qry_doc.text_element import TextElement, TextAlignment
from qry_doc.cover_builder import CoverBuilder, CoverConfig
from qry_doc.chart_config import ChartConfig, ChartTypeEnum, VALID_CHART_TYPES
from qry_doc.report_preset import ReportPreset, ReportPresetType
from qry_doc.template_builder import TemplateBuilder
from qry_doc.ai_builder import AIBuilder, DataSummary, ChartSuggestion

# Asset management
from qry_doc.asset_manager import AssetManager

# Exceptions
from qry_doc.exceptions import (
    QryDocError,
    QueryError,
    ExportError,
    ReportError,
    DataSourceError,
    ValidationError,
)

# Public API
__all__ = [
    # Version
    "__version__",
    # Main class
    "QryDoc",
    # Templates and configuration
    "ReportTemplate",
    "SectionType",
    "SectionConfig",
    "LogoPosition",
    "DEFAULT_TEMPLATE",
    "CORPORATE_TEMPLATE",
    "MINIMAL_TEMPLATE",
    "A4_TEMPLATE",
    # New builder components
    "TextElement",
    "TextAlignment",
    "CoverBuilder",
    "CoverConfig",
    "ChartConfig",
    "ChartTypeEnum",
    "VALID_CHART_TYPES",
    "ReportPreset",
    "ReportPresetType",
    "TemplateBuilder",
    "AIBuilder",
    "DataSummary",
    "ChartSuggestion",
    # Asset management
    "AssetManager",
    # Exceptions
    "QryDocError",
    "QueryError",
    "ExportError",
    "ReportError",
    "DataSourceError",
    "ValidationError",
]
