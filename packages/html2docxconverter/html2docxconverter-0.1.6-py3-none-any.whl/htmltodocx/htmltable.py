from __future__ import annotations
from typing import TYPE_CHECKING, Tuple
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from htmltodocx.colors import get_color_hex

from htmltodocx.parse_style import (
    css_length_to_inches,
    parse_style_css,
)
from htmltodocx.schemas import ConfigSchema

if TYPE_CHECKING:
    from docx.table import Table, _Row, _Cell
    from bs4 import Tag
    from htmltodocx.parse_style import ParserStyle


def apply_row_height(row: _Row, height: str | int) -> None:
    if isinstance(height, str):
        height_twips = int(css_length_to_inches(height.strip()) * 1440)
    else:
        height_twips = height
    tr_pr = row._tr.get_or_add_trPr()
    tr_height = OxmlElement("w:trHeight")
    tr_height.set(qn("w:val"), str(height_twips))
    tr_height.set(qn("w:hRule"), "exact")
    tr_pr.append(tr_height)


class TableStyleApplier:
    def __init__(self, table_tag: Tag, table: Table):
        self.style_dict = parse_style_css(table_tag.get("style", ""))
        self.table_tag = table_tag
        self.table = table
        self.pr = table._tbl.tblPr
        self.return_style = {}

    def apply(self) -> dict:
        self._apply_width()
        self._apply_colgroup_widths()
        self._apply_cols_styles()
        self._apply_float()
        return self.return_style

    def _get_or_create(self, tag_name: str) -> OxmlElement:
        el = self.pr.find(qn(tag_name))
        if el is None:
            el = OxmlElement(tag_name)
            self.pr.append(el)
        return el

    def _apply_float(self) -> None:
        float_val = self.style_dict.get("float", "").strip().lower()
        if float_val not in ("left", "right"):
            return
        alignment_el = self._get_or_create("w:jc")
        if float_val == "left":
            alignment_el.set(qn("w:val"), "left")
        elif float_val == "right":
            alignment_el.set(qn("w:val"), "right")

    def _apply_cols_styles(self) -> None:
        height_val = self.style_dict.get("height")
        border_style = self.style_dict.get("border-style")
        border_width = self.style_dict.get("border-width")
        background_color = self.style_dict.get("background-color")
        border = self.style_dict.get("border")
        border_color = self.style_dict.get("border-color")
        if height_val:
            self.return_style["height"] = height_val
        if border_style:
            self.return_style["border-style"] = border_style
        if border_width:
            self.return_style["border-width"] = border_width
        if background_color:
            self.return_style["background-color"] = background_color
        if border:
            self.return_style["border"] = border
        if border_color:
            self.return_style["border-color"] = border_color

    def _apply_width(self) -> None:
        width_val = self.style_dict.get("width")
        if not width_val:
            return
        width_twips = int(css_length_to_inches(width_val.strip()) * 1440)
        width_el = self._get_or_create("w:tblW")
        width_el.set(qn("w:type"), "dxa")
        width_el.set(qn("w:w"), str(width_twips))

    def _apply_colgroup_widths(self) -> None:
        if not hasattr(self.table, "columns"):
            return

        colgroup = self.table_tag.find("colgroup")
        if colgroup:
            cols = colgroup.find_all("col")
            for i, col in enumerate(cols):
                if i >= len(self.table.columns):
                    break
                style = col.get("style", "")
                style_dict = parse_style_css(style)
                width_val = style_dict.get("width")
                if width_val:
                    width_twips = int(css_length_to_inches(width_val.strip()) * 1440)
                    for cell in self.table.columns[i].cells:
                        tc_pr = cell._tc.get_or_add_tcPr()
                        tc_w = OxmlElement("w:tcW")
                        tc_w.set(qn("w:w"), str(width_twips))
                        tc_w.set(qn("w:type"), "dxa")
                        tc_pr.append(tc_w)


class TableCellStyleApplier:
    def __init__(
            self,
            parser_style: ParserStyle,
            config: ConfigSchema,
            layout_table: bool = False,
            table_style: dict = None,
    ):
        self.pr = None
        self.layout_table = layout_table
        self.config = config
        self.table_style = table_style
        self.parser_style = parser_style

    def apply(self,
              cell_tag: Tag | dict,
              cell: _Cell,
              ) -> str:
        style_dict = parse_style_css(cell_tag.get("style", ""))
        self.pr = cell._tc.get_or_add_tcPr()
        self._apply_background(style_dict)
        self._apply_border(style_dict)
        self._apply_width(style_dict)
        self._apply_text_align(cell, style_dict)
        self._apply_vertical_align(style_dict)
        return style_dict.get("height")

    def _get_or_create(self, tag_name: str) -> OxmlElement:
        el = self.pr.find(qn(tag_name))
        if el is None:
            el = OxmlElement(tag_name)
            self.pr.append(el)
        return el

    def _apply_width(self, style_dict: dict) -> None:
        width_val = style_dict.get("width")
        if not width_val:
            return
        width_val = width_val.strip()
        width_twips = int(css_length_to_inches(width_val) * 1440)
        tc_w = OxmlElement("w:tcW")
        tc_w.set(qn("w:w"), str(width_twips))
        tc_w.set(qn("w:type"), "dxa")
        self.pr.append(tc_w)

    def _apply_background(self, style_dict: dict) -> None:
        use_dict = None
        if self.table_style and "background-color" in self.table_style:
            use_dict = self.table_style

        if "background-color" in style_dict:
            use_dict = style_dict

        if use_dict:
            color = get_color_hex(use_dict["background-color"].strip())
            shading = OxmlElement("w:shd")
            shading.set(qn("w:val"), "clear")
            shading.set(qn("w:color"), "auto")
            shading.set(qn("w:fill"), color)
            self.pr.append(shading)

    def _default_border_style(self) -> Tuple[str, str, str]:
        if self.layout_table:
            return "", "", ""
        default_table_style = self.config.default_settings.table_style
        if default_table_style:
            width = default_table_style.width
            style = default_table_style.style
            color = default_table_style.color
        else:
            width, style, color = "1pt", "single", "000000"
        if self.table_style:
            width, style, color = self.parser_style.css_table_style(width, style, color, self.table_style)
        return width, style, color

    def _apply_border(self, style_dict: dict) -> None:
        borders = self._get_or_create("w:tcBorders")
        width, style, color = self._default_border_style()
        if style_dict:
            width, style, color = self.parser_style.css_table_style(width, style, color, style_dict)

        if width.endswith("px"):
            sz = str(int(float(width[:-2]) * 8))
        elif width.endswith("pt"):
            sz = str(int(float(width[:-2]) * 8))
        else:
            sz = "8"

        for side in self.config.border_side:
            el = OxmlElement(f"w:{side}")
            el.set(qn("w:val"), style)
            el.set(qn("w:sz"), sz)
            el.set(qn("w:space"), "0")
            el.set(qn("w:color"), color)
            borders.append(el)

        self.pr.append(borders)

    def _apply_text_align(self, cell: _Cell, style_dict: dict) -> None:
        align_val = style_dict.get("text-align", "").strip()
        if align_val:
            for p in cell.paragraphs:
                p.alignment = self.config.align_map.get(align_val, self.config.default_settings.align_paragraph)

    def _apply_vertical_align(self, style_dict: dict) -> None:
        v_align_val = style_dict.get("vertical-align", "").strip().lower()
        v_align = OxmlElement("w:vAlign")
        if v_align_val in self.config.vertical_align_map:
            v_align.set(qn("w:val"), self.config.vertical_align_map[v_align_val])
        else:
            v_align.set(qn("w:val"), self.config.default_settings.vertical_align)
        self.pr.append(v_align)



