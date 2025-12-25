from typing import Any, Dict, Optional

import fitz
from sayou.core.registry import register_component

from ..interfaces.base_ocr import BaseOCR
from ..interfaces.base_parser import BaseDocumentParser
from ..models import (
    BaseElement,
    BoundingBox,
    Document,
    ElementMetadata,
    ImageElement,
    Page,
    TextElement,
)


@register_component("parser")
class PdfParser(BaseDocumentParser):
    """
    (Tier 2) Parser for PDF files using PyMuPDF (fitz).

    Supports high-fidelity extraction of text blocks and images.
    Features 'Smart Scan Detection': automatically applies OCR to whole pages
    if extracted text content is insufficient.
    """

    component_name = "PdfParser"
    SUPPORTED_TYPES = [".pdf"]

    @classmethod
    def can_handle(cls, file_bytes: bytes, file_name: str) -> float:
        """
        Checks for PDF signature (%PDF) or extension.
        """
        if file_bytes.startswith(b"%PDF"):
            return 1.0
        if file_name.lower().endswith(".pdf"):
            return 0.8
        return 0.0

    def __init__(self, ocr_engine: Optional[BaseOCR] = None):
        """
        Initialize the parser with an optional OCR engine.
        """
        super().__init__()
        if ocr_engine:
            self.set_ocr_engine(ocr_engine)

    def _do_parse(self, file_bytes: bytes, file_name: str, **kwargs) -> Document:
        """
        Parse PDF bytes into a structured Document.

        Args:
            file_bytes (bytes): PDF file content.
            file_name (str): Original filename.
            **kwargs:
                - ocr_dpi (int): Resolution for rendering pages for OCR (default: 200).

        Returns:
            Document: A document object with 'doc_type="pdf"'.
        """
        # 1. PDF 로드
        doc = self._load_document(file_bytes)
        pages_list = []

        # 2. 페이지 순회
        for page_num in range(doc.page_count):
            page_obj = self._process_page(doc, page_num, file_name)
            pages_list.append(page_obj)

        # 3. TOC(목차) 추출
        toc_list = []
        try:
            toc = doc.get_toc()
            for item in toc:
                level, title, page_num = item
                toc_list.append({"level": level, "title": title, "page_num": page_num})
        except Exception as e:
            self._log(f"Failed to extract TOC: {e}", level="warning")

        doc.close()

        # 4. 최종 Document 반환
        return Document(
            file_name=file_name,
            file_id=file_name,
            doc_type="pdf",
            page_count=len(pages_list),
            pages=pages_list,
            toc=toc_list,
        )

    def _load_document(self, file_bytes: bytes) -> fitz.Document:
        """Safe wrapper to open PDF stream with fitz."""
        try:
            return fitz.open(stream=file_bytes, filetype="pdf")
        except Exception as e:
            raise ValueError(f"fitz failed to open PDF: {e}")

    def _process_page(
        self, doc: fitz.Document, page_num: int, file_name: str, **kwargs
    ) -> Page:
        """
        Process a single PDF page.

        Checks for 'scanned page' condition (empty text) and triggers
        full-page OCR if necessary. Otherwise, iterates through layout blocks.

        Args:
            doc (fitz.Document): The open document handle.
            page_num (int): 0-based page index.
            file_name (str): Filename for metadata.

        Returns:
            Page: Constructed Page object with elements.
        """
        page = doc.load_page(page_num)
        elements_list = []
        page_text_dump = page.get_text()
        ocr_applied = False

        # 텍스트가 거의 없다면 (스캔본 의심)
        if not page_text_dump.strip() and self.ocr_engine:
            self._log(f"Page {page_num+1} seems to be scanned. Applying full-page OCR.")
            try:
                # 페이지를 고해상도 이미지로 렌더링
                pix = page.get_pixmap(dpi=kwargs.get("ocr_dpi", 200))
                img_bytes = pix.tobytes("png")
                ocr_text = self.ocr_engine.ocr(img_bytes, **kwargs)

                if ocr_text:
                    # 페이지 전체를 하나의 TextElement로 생성
                    full_page_bbox = BoundingBox(
                        x0=0, y0=0, x1=page.rect.width, y1=page.rect.height
                    )
                    elements_list.append(
                        TextElement(
                            id=f"p{page_num+1}:full_ocr",
                            type="text",
                            bbox=full_page_bbox,
                            meta=ElementMetadata(
                                page_num=page_num + 1, id=f"p{page_num+1}:full_ocr"
                            ),
                            text=ocr_text,
                        )
                    )
                    page_text_dump = ocr_text
                    ocr_applied = True

            except Exception as e:
                self._log(
                    f"Full-page OCR failed for page {page_num+1}: {e}", level="warning"
                )

        if not ocr_applied:
            blocks = page.get_text("dict", flags=fitz.TEXTFLAGS_DICT, sort=True).get(
                "blocks", []
            )
            for block in blocks:
                element = self._create_element_from_block(
                    block, page_num, file_name, **kwargs
                )
                if element:
                    elements_list.append(element)

        return Page(
            page_num=page_num + 1,
            width=page.rect.width,
            height=page.rect.height,
            elements=elements_list,
            text=page_text_dump,
        )

    def _create_element_from_block(
        self, block: Dict[str, Any], page_num: int, file_name: str, **kwargs
    ) -> Optional[BaseElement]:
        """
        Factory method to convert a PyMuPDF text/image block dict into a Pydantic Element.
        """
        b_type = block.get("type")
        bbox = block.get("bbox")

        pydantic_bbox = BoundingBox(x0=bbox[0], y0=bbox[1], x1=bbox[2], y1=bbox[3])

        meta = ElementMetadata(
            page_num=page_num + 1, id=f"p{page_num}:b{block.get('number', 0)}"
        )

        # Type 0: Text Block
        if b_type == 0:
            return self._process_text_block(block, pydantic_bbox, meta)

        # Type 1: Image Block
        elif b_type == 1:
            return self._process_image_block(block, pydantic_bbox, meta, **kwargs)

        return None

    def _process_text_block(
        self, block: Dict, bbox: BoundingBox, meta: ElementMetadata
    ) -> Optional[TextElement]:
        """Convert a text block dictionary into a TextElement."""
        block_text = ""
        # TODO: High-Fidelity (v0.1.0+) - 폰트/스타일 정보 추출
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                block_text += span.get("text", "")
            block_text += " "

        block_text = block_text.strip()
        if not block_text:
            return None

        return TextElement(
            id=meta.id,
            bbox=bbox,
            text=block_text,
            meta=meta,
            # raw_attributes={"style": span.get("font")...} # v0.1.0
        )

    def _process_image_block(
        self, block: Dict, bbox: BoundingBox, meta: ElementMetadata, **kwargs
    ) -> Optional[ImageElement]:
        """Convert an image block dictionary into an ImageElement (with optional OCR)."""
        try:
            image_bytes = block.get("image")
            if not image_bytes:
                return None
            ocr_enabled = kwargs.get("ocr_images", True)

            return self._process_image_data(
                image_bytes=image_bytes,
                img_format=block.get("ext", "png"),
                elem_id=meta.id,
                page_num=meta.page_num,
                bbox=bbox,
                ocr_enabled=ocr_enabled,
            )

        except Exception as e:
            self._log(f"Failed to process image block: {e}")
            return None
