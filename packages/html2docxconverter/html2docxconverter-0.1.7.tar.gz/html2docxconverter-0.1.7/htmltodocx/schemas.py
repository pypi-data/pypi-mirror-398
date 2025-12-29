from dataclasses import dataclass
from typing import Optional

from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.shared import RGBColor

@dataclass
class DefaultTableStyleSchema:
    width: str
    style: str
    color: str

@dataclass
class DefaultConfigSchema:
    align_paragraph: WD_PARAGRAPH_ALIGNMENT
    align_image: WD_PARAGRAPH_ALIGNMENT
    vertical_align: str
    table_style: Optional[DefaultTableStyleSchema] = None

@dataclass
class ConfigSchema:
    align_map: dict[str, WD_PARAGRAPH_ALIGNMENT]
    align_image_class_map: dict[str, WD_PARAGRAPH_ALIGNMENT]
    vertical_align_map: dict[str, str]
    border_side: list[str]
    border_style: dict[str, str]
    default_settings: DefaultConfigSchema

@dataclass
class StyleSchema:
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strike: bool = False
    subscript: bool = False
    superscript: bool = False
    font_size: Optional[int] = None
    color: Optional[RGBColor] = None
    background_color: Optional[str] = None
