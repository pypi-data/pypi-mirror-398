from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

# ==============================================================================
# 1. Atom (최소 단위) - Common Schema 기반
# ==============================================================================


class BoundingBox(BaseModel):
    """
    Represents a rectangular region on a page using absolute coordinates.

    Units depend on the source format (e.g., Points for PDF, EMUs for PPTX).
    Values are NOT normalized to 0.0-1.0 range.

    Structure:
    - x0: Left
    - y0: Top
    - x1: Right
    - y1: Bottom
    """

    x0: float = 0.0
    y0: float = 0.0
    x1: float = 0.0
    y1: float = 0.0


class TextStyle(BaseModel):
    """
    Captures high-fidelity font and styling information for text elements.

    Used to preserve the visual appearance of text, which can be useful for
    rendering or semantic analysis (e.g., detecting emphasis).
    """

    font_name: Optional[str] = None
    font_size: Optional[float] = None
    color: Optional[str] = None
    is_bold: bool = False
    is_italic: bool = False
    is_underlined: bool = False


class ElementMetadata(BaseModel):
    """
    Common metadata shared by all document elements.

    Stores contextual information like the page number where the element appears,
    a unique identifier, and optionally a hyperlink if the element is clickable.
    """

    model_config = ConfigDict(extra="allow")  # 정의되지 않은 필드도 허용

    page_num: int
    id: Optional[str] = None
    link: Optional[str] = None


# ==============================================================================
# 2. Elements (콘텐츠 요소) - 모든 문서 공통
# ==============================================================================


class BaseElement(BaseModel):
    """
    The abstract base class for all document content blocks.

    Every piece of content extracted from a document (text, image, table, etc.)
    inherits from this class. It provides a common interface for ID, type,
    location (bbox), and raw attributes specific to the source format.
    """

    id: str
    type: str
    bbox: Optional[BoundingBox] = None

    # 원본 스키마의 자잘한 속성들(z-order, rotation 등) 보존
    raw_attributes: Dict[str, Any] = {}
    model_config = ConfigDict(extra="allow")

    @property
    def text(self) -> str:
        """Returns the textual representation of the element."""
        return ""


class TextElement(BaseElement):
    """
    Represents a block of text.

    This includes paragraphs, headings, list items, and other textual content.
    It may include styling information via the `style` field.
    """

    type: Literal["text"] = "text"
    # text: str
    style: Optional[TextStyle] = None
    meta: ElementMetadata


class TableCell(BaseModel):
    """
    Represents a single cell within a TableElement.

    Contains the text content of the cell and layout information like row/column
    spanning, as well as semantic flags (e.g., is_header).
    """

    text: str
    row_span: int = 1
    col_span: int = 1
    is_header: bool = False
    bbox: Optional[BoundingBox] = None


class TableElement(BaseElement):
    """
    Represents a tabular data structure.

    Stores data in two formats:
    1. `data`: A simplified 2D list of strings (LLM-friendly).
    2. `cells`: A detailed list of `TableCell` objects (High-fidelity layout).
    """

    type: Literal["table"] = "table"
    data: List[List[str]]
    cells: List[List[TableCell]] = []
    caption: Optional[str] = None
    meta: ElementMetadata

    @property
    def text(self) -> str:
        """Returns a CSV-like string representation of the table."""
        if not self.data:
            return ""
        return "\n".join(["\t".join(row) for row in self.data])


class ImageElement(BaseElement):
    """
    Represents an image embedded in the document.

    Can store the image data as a Base64 string (`image_base64`), a URL (`image_url`),
    or extracted text via OCR (`ocr_text`).
    """

    type: Literal["image"] = "image"
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    caption: Optional[str] = None
    ocr_text: Optional[str] = None
    meta: ElementMetadata

    @property
    def text(self) -> str:
        """Returns OCR text if available."""
        return self.ocr_text or self.caption or ""


class ChartElement(BaseElement):
    """
    Represents a chart or graph.

    Since visual charts are hard to parse directly, this element focuses on
    extracting the underlying data or a textual description (`text_representation`)
    that describes the chart's content (e.g., series names, data points).
    """

    type: Literal["chart"] = "chart"
    chart_title: Optional[str] = None
    chart_type: Optional[str] = None
    text_representation: Optional[str] = None
    meta: ElementMetadata

    @property
    def text(self) -> str:
        """Returns text representation of the chart."""
        return self.text_representation or self.chart_title or ""


# ==============================================================================
# 3. Containers (그릇) - 각 스키마 특화 영역
# ==============================================================================


class BasePage(BaseModel):
    """
    Abstract base class for a single page or slide container.

    Holds dimensions (width, height) and a list of content elements found
    within this container.
    """

    page_num: int
    width: Optional[float] = None
    height: Optional[float] = None
    elements: List[Union[TextElement, TableElement, ImageElement, ChartElement]] = []


class Page(BasePage):
    """
    Represents a sequential page in flow documents (PDF, Word).

    Unlike generic pages, this includes specific areas for headers and footers,
    and a `text` field containing the raw text dump of the page.
    """

    header_elements: List[
        Union[TextElement, TableElement, ImageElement, ChartElement]
    ] = []
    footer_elements: List[
        Union[TextElement, TableElement, ImageElement, ChartElement]
    ] = []
    text: Optional[str] = None


class Slide(BasePage):
    """
    Represents a slide in presentation documents (PowerPoint).

    Includes specific features for presentations, such as speaker notes (`note_text`)
    and master slide references.
    """

    has_notes: bool = False
    note_text: Optional[str] = None
    master_slide_id: Optional[str] = None


class Sheet(BasePage):
    """
    Represents a worksheet in spreadsheet documents (Excel).

    Maps the concept of a 'page' to an infinite canvas of cells.
    Includes metadata like the sheet name and visibility state.
    """

    sheet_name: str
    is_hidden: bool = False
    sheet_index: int


# ==============================================================================
# 4. The Document (Root) - 통합 인터페이스
# ==============================================================================


# class Page(BaseModel):
#     page_num: int
#     width: Optional[float] = None
#     height: Optional[float] = None
#     elements: List[Union[TextElement, TableElement, ImageElement]] = []
#     text: Optional[str] = None


class DocumentMetadata(BaseModel):
    """
    Global metadata for the entire document.

    Includes standard properties like title, author, and creation dates,
    as well as a dictionary for any format-specific extra metadata.
    """

    title: Optional[str] = None
    author: Optional[str] = None
    created_at: Optional[str] = None
    modified_at: Optional[str] = None
    source_path: Optional[str] = None
    extra: Dict[str, Any] = {}


class Document(BaseModel):
    """
    The root object representing a fully parsed document.

    This unified structure serves as the standard output for all `sayou-document` parsers.
    It acts as a container for pages (or slides/sheets) and global metadata,
    abstracting away the differences between PDF, DOCX, PPTX, and XLSX formats.
    """

    file_name: str
    file_id: str
    doc_type: Literal["pdf", "word", "slide", "sheet", "unknown"]

    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)
    page_count: int = 0

    pages: List[Union[Page, Slide, Sheet]] = []

    toc: List[Dict[str, Any]] = []  # Bookmarks/Table of Contents
    links: List[Dict[str, Any]] = []  # Global Hyperlinks
