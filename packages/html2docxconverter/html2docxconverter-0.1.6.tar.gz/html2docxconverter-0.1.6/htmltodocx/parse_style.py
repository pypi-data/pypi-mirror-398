from __future__ import annotations

from typing import TYPE_CHECKING

from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import RGBColor, Pt
from docx.text.paragraph import Paragraph

from htmltodocx.colors import get_color_hex, get_color_rgb
from htmltodocx.schemas import StyleSchema, ConfigSchema

if TYPE_CHECKING:
    from bs4 import Tag
    from docx.text.run import Run
    from typing import Optional, Tuple

def parse_style_css(style_str: str) -> dict:
    if not style_str:
        return {}
    return dict([s.strip().split(":") for s in style_str.split(";") if ":" in s])


def css_length_to_inches(value: str) -> float | int:
    if value.endswith("px"):
        return int(value[:-2]) * 0.0104
    if value.endswith("pt"):
        return int(value[:-2]) / 72
    if value.endswith("cm"):
        return int(value[:-2]) / 2.54
    if value.endswith("%"):
        return 6.0 * (float(value.strip("%")) / 100.0)  # assume full width 6.0 in
    try:
        return float(value)
    except ValueError:
        return 0.0


def apply_shading(paragraph_run: Run, color: str) -> None:
    rPr = paragraph_run._r.get_or_add_rPr()
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), color)
    rPr.append(shading)


def parse_style_selector(tag: Tag, styles: Optional[StyleSchema] = None) -> StyleSchema:
    if not styles:
        styles = StyleSchema()
    tag_name = tag.name
    # Жирный
    if tag_name in ['strong', 'b']:
        styles.bold = True
    # Курсив
    elif tag_name in ['em', 'i']:
        styles.italic = True
    # Подчёркивание
    elif tag_name == 'u':
        styles.underline = True
    # Зачёркивание
    elif tag_name in ['s', 'strike', 'del']:
        styles.strike = True
    # Надстрочный
    elif tag_name == 'sup':
        styles.superscript = True
    # Подстрочный
    elif tag_name == 'sub':
        styles.subscript = True

    if tag_name and "style" in tag.attrs:
        css_style = parse_style_css(tag["style"])
        if "font-size" in css_style:
            fs = str(css_style["font-size"])
            if fs.endswith("px"):
                styles.font_size = int(fs[:-2])
        if "color" in css_style:
            styles.color = RGBColor(*get_color_rgb(css_style['color']))
        if "background-color" in css_style:
            styles.background_color = get_color_hex(css_style['background-color'])
    return styles

def apply_styles_to_text(paragraph_run: Run, styles: StyleSchema) -> None:
    paragraph_run.bold = styles.bold
    paragraph_run.italic = styles.italic
    paragraph_run.underline = styles.underline
    paragraph_run.font.strike = styles.strike
    paragraph_run.font.subscript = styles.subscript
    paragraph_run.font.superscript = styles.superscript
    if styles.font_size:
        paragraph_run.font.size = Pt(styles.font_size)
    if styles.color:
        paragraph_run.font.color.rgb = styles.color
    if styles.background_color:
        apply_shading(paragraph_run, styles.background_color)


class ParserStyle:
    def __init__(self, config: ConfigSchema) -> None:
        self.border_style = config.border_style
        self.align_map = config.align_map
        self.align_image_class_map = config.align_image_class_map
        self.default_settings = config.default_settings

    def parse_border(self, border_str: str) -> Tuple[str, str, Optional[str]]:
        width = self.default_settings.table_style.width
        style = self.default_settings.table_style.style
        color = self.default_settings.table_style.color
        parts = border_str.strip().split()
        if len(parts) == 1:
            width = parts[0]
        elif len(parts) == 2:
            width = parts[0]
            style = self.border_style.get(parts[1].strip(), style)
        elif len(parts) > 3:
            width = parts[0]
            style = self.border_style.get(parts[1].strip(), style)
            color = get_color_hex(" ".join(parts[2: len(parts)]))
        return width, style, color

    def css_table_style(self, width: str, style: str, color: str, style_dict: dict) -> tuple:
        default_style = self.default_settings.table_style.style
        if "border" in style_dict:
            width, bs, color = self.parse_border(style_dict["border"])
            style = self.border_style.get(bs.strip(), default_style)
        if "border-width" in style_dict:
            width = style_dict["border-width"].strip()
        if "border-style" in style_dict:
            style = self.border_style.get(style_dict["border-style"].strip(), default_style)
        if "border-color" in style_dict:
            color = get_color_hex(style_dict["border-color"].strip())
        return width, style, color

    def apply_position_paragraph(self, tag: Tag, paragraph_run: Paragraph) -> None:
        if "style" in tag.attrs and "text-align" in tag["style"]:
            styles = tag['style']
            if "left" in styles:
                paragraph_run.alignment = self.align_map["left"]
            elif "right" in styles:
                paragraph_run.alignment = self.align_map["right"]
            elif "center" in styles:
                paragraph_run.alignment = self.align_map["center"]
            elif "justify" in styles:
                paragraph_run.alignment = self.align_map["justify"]
        else:
            paragraph_run.alignment = self.default_settings.align_paragraph

    def apply_position_image(self, tag: Tag, paragraph_run: Paragraph) -> None:
        if "class" in tag.attrs:
            cl = tag.attrs['class']
            for key, val in self.align_image_class_map.items():
                if key in cl:
                    paragraph_run.alignment = val
                    return
            paragraph_run.alignment = self.default_settings.align_image



