from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

from htmltodocx.schemas import ConfigSchema, DefaultTableStyleSchema, DefaultConfigSchema

align_map = {
    "left": WD_PARAGRAPH_ALIGNMENT.LEFT,
    "center": WD_PARAGRAPH_ALIGNMENT.CENTER,
    "right": WD_PARAGRAPH_ALIGNMENT.RIGHT,
    "justify": WD_PARAGRAPH_ALIGNMENT.JUSTIFY,
}

align_image_class_map = {
    "image-style-block-align-left": WD_PARAGRAPH_ALIGNMENT.LEFT,
    "image-style-block-align-right": WD_PARAGRAPH_ALIGNMENT.RIGHT,
    "image-style-block-align-center": WD_PARAGRAPH_ALIGNMENT.CENTER,
}

vertical_align_map = {"top": "top", "middle": "center", "bottom": "bottom"}

border_side = ["top", "left", "bottom", "right"]

border_style = {
    "none": "nil",
    "solid": "single",
    "dotted": "dotted",
    "dashed": "dash",
    "double": "double",
    "groove": "threeDEmboss",
    "ridge": "threeDEngrave",
    "inset": "inset",
    "outset": "outset",
}

default_settings = DefaultConfigSchema(
    align_paragraph=WD_PARAGRAPH_ALIGNMENT.JUSTIFY,
    align_image=WD_PARAGRAPH_ALIGNMENT.CENTER,
    vertical_align='center',
    table_style=DefaultTableStyleSchema(
width="1pt", style="single", color="000000"
    )
)

base_config = ConfigSchema(
    align_map=align_map,
    align_image_class_map=align_image_class_map,
    vertical_align_map=vertical_align_map,
    border_side=border_side,
    border_style=border_style,
    default_settings=default_settings
)