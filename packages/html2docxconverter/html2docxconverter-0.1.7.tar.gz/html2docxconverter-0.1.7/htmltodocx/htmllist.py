from __future__ import annotations
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from docx import Document


class HTMLListHelper:
    def __init__(self, doc: Document):
        self.doc = doc
        self.list_num_counter = 10

    def add_numbering_definition(self, is_ordered=True):
        numbering_part = self.doc.part.numbering_part
        abstract_num = OxmlElement("w:abstractNum")
        abstract_num.set(qn("w:abstractNumId"), str(self.list_num_counter))
        lvl = OxmlElement("w:lvl")
        lvl.set(qn("w:ilvl"), "0")
        num_fmt = OxmlElement("w:numFmt")
        num_fmt.set(qn("w:val"), "decimal" if is_ordered else "bullet")
        lvl.append(num_fmt)
        lvl_text = OxmlElement("w:lvlText")
        lvl_text.set(qn("w:val"), "%1." if is_ordered else "•")
        lvl.append(lvl_text)
        start = OxmlElement("w:start")
        start.set(qn("w:val"), "1")
        lvl.append(start)
        abstract_num.append(lvl)
        numbering_part._element.append(abstract_num)
        num = OxmlElement("w:num")
        num.set(qn("w:numId"), str(self.list_num_counter))
        abstract_num_id = OxmlElement("w:abstractNumId")
        abstract_num_id.set(qn("w:val"), str(self.list_num_counter))
        num.append(abstract_num_id)
        numbering_part._element.append(num)
        current_num_id = self.list_num_counter
        self.list_num_counter += 1
        return current_num_id

    def add_list_item(self, paragraph, is_ordered=True, num_id=None):
        if num_id is None:
            num_id = self.add_numbering_definition(is_ordered)
        style_name = "List Number" if is_ordered else "List Bullet"
        paragraph.style = style_name
        p_pr = paragraph._p.get_or_add_pPr()
        num_pr = OxmlElement("w:numPr")
        i_lvl = OxmlElement("w:ilvl")
        i_lvl.set(qn("w:val"), "0")
        el_num_id = OxmlElement("w:numId")
        el_num_id.set(qn("w:val"), str(num_id))
        num_pr.append(i_lvl)
        num_pr.append(el_num_id)
        p_pr.append(num_pr)
