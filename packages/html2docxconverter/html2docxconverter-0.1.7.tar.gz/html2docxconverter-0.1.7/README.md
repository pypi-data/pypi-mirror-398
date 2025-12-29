# Библиотека конвертации HTML в DOCX

Python-библиотека для преобразования HTML-контента в документы Word (.docx) с поддержкой таблиц, списков, изображений и CSS-стилей.

## Установка

```bash
pip install html2docxconverter
```
```bash
uv add html2docxconverter
```

## Поддерживаемые HTML-теги

### Основные теги
- **`<p>`** - абзацы текста
- **`<figure>`** - контейнеры для изображений
- **`<ul>`** - неупорядоченные списки
- **`<ol>`** - упорядоченные списки
- **`<li>`** - элементы списков
- **`<table>`** - таблицы
- **`<tr>`** - строки таблицы
- **`<td>`** - ячейки таблицы
- **`<th>`** - заголовочные ячейки таблицы
- **`<colgroup>`** - группировка столбцов таблицы
- **`<col>`** - определение столбца таблицы
- **`<tbody>`** - тело таблицы

### Теги форматирования текста
- **`<strong>`**, **`<b>`** - жирный текст
- **`<em>`**, **`<i>`** - курсив
- **`<u>`** - подчеркнутый текст
- **`<s>`**, **`<strike>`**, **`<del>`** - зачеркнутый текст
- **`<sup>`** - верхний индекс
- **`<sub>`** - нижний индекс
- **`<span>`** - контейнер для стилизации текста

## Поддерживаемые CSS-стили

### Стили текста
- **`color`** - цвет текста (имена цветов, hex, rgb)
- **`background-color`** - выделение цветом (имена цветов, hex, rgb)
- **`font-size`** - размер шрифта (px, pt, em, %)
- **`text-align`** - выравнивание текста (left, right, center, justify)
- **`vertical-align`** - вертикальное выравнивание (top, middle, bottom)

### Стили таблиц и ячеек
- **`width`** - ширина таблицы/ячейки (px, %)
- **`height`** - высота строки/ячейки (px)
- **`background-color`** - цвет фона таблицы/ячейки
- **`border`** - граница (ширина стиль цвет)
- **`border-width`** - ширина границы
- **`border-style`** - стиль границы (solid, single)
- **`border-color`** - цвет границы
- **`float`** - позиционирование таблицы (left, right)

### За основу при создании HTML контента использовался
[CKEditor](https://ckeditor.com/)

## Пример использования

```python
from docx import Document
from htmltodocx import HTMLtoDocx

# Создание нового документа
doc = Document()

# HTML-контент для конвертации
html_content = """
<p>Это <strong>жирный</strong> и <em>курсивный</em> текст.</p>
<ul>
    <li>Первый элемент</li>
    <li>Второй элемент</li>
</ul>
"""

# Конвертация HTML в DOCX
converter = HTMLtoDocx(doc)
converted_doc = converter.parse_html(html_content)

# Сохранение документа
converted_doc.save("output.docx")
```

## Настройки форматирования

```python
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from htmltodocx.schemas import ConfigSchema, DefaultTableStyleSchema, DefaultConfigSchema
from docx import Document
from htmltodocx import HTMLtoDocx

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
# HTML-контент для конвертации
html_content = """
<p>Это <strong>жирный</strong> и <em>курсивный</em> текст.</p>
<ul>
    <li>Первый элемент</li>
    <li>Второй элемент</li>
</ul>
"""

# Конвертация HTML в DOCX
doc = Document()
converter = HTMLtoDocx(doc, config=base_config)
converted_doc = converter.parse_html(html_content)

# Сохранение документа
converted_doc.save("output.docx")
```


## Лицензия

MIT License

