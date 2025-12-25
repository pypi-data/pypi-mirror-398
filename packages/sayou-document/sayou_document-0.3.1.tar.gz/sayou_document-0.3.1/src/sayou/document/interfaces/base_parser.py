from abc import abstractmethod
from typing import List, Optional

from sayou.core.base_component import BaseComponent
from sayou.core.decorators import measure_time

from ..core.exceptions import ParserError
from ..interfaces.base_ocr import BaseOCR
from ..models import BoundingBox, Document, ElementMetadata, ImageElement


class BaseDocumentParser(BaseComponent):
    """
    (Tier 1) Abstract base class for all document parsers.

    Provides common functionality for logging, error handling, and OCR engine integration.
    Implements the Template Method pattern via `parse` -> `_do_parse`.
    """

    component_name = "BaseDocumentParser"
    SUPPORTED_TYPES: List[str] = []

    def __init__(self, ocr_engine=None):
        super().__init__()
        self.ocr_engine: Optional[BaseOCR] = ocr_engine

    def set_ocr_engine(self, ocr_engine: Optional[BaseOCR]):
        """
        Inject an OCR engine for processing scanned images.

        Args:
            ocr_engine (BaseOCR): The OCR engine instance.
        """
        self.ocr_engine = ocr_engine
        if ocr_engine:
            self._log(f"OCR Engine '{ocr_engine.component_name}' attached.")

    @classmethod
    def can_handle(cls, file_bytes: bytes, file_name: str) -> float:
        """
        Determines if the parser can handle the given file based on content (magic bytes) and name.

        Args:
            file_bytes (bytes): The beginning bytes of the file.
            file_name (str): The name of the file.

        Returns:
            float: Confidence score (0.0 to 1.0).
        """
        return 0.0

    @measure_time
    def parse(self, file_bytes: bytes, file_name: str, **kwargs) -> Optional[Document]:
        """
        Execute the parsing process.

        Args:
            file_bytes (bytes): Binary content of the file.
            file_name (str): Original filename (used for extension detection).
            **kwargs: Additional parsing options.

        Returns:
            Document: The parsed structured document object, or None if failed.

        Raises:
            ParserError: If parsing logic encounters a critical error.
        """
        self._emit(
            "on_start",
            input_data={"filename": file_name, "parser": self.component_name},
        )
        self._log(f"Parsing file: {file_name} ({len(file_bytes)} bytes)")

        if not file_bytes:
            self._log("Received empty file bytes.", level="warning")
            return None

        try:
            tesseract_path = kwargs.get("tesseract_path")
            document = self._do_parse(
                file_bytes, file_name, tesseract_path=tesseract_path, **kwargs
            )

            if document:
                self._log(
                    f"Successfully extracted {len(document.pages)} pages from {file_name}."
                )
                self._emit("on_finish", result_data=document, success=True)
            else:
                self._log("Parser returned None.", level="warning")
                self._emit("on_finish", result_data=None, success=False)

            return document

        except Exception as e:
            self._emit("on_error", error=e)
            wrapped_error = ParserError(
                f"[{self.component_name}] Failed to parse {file_name}: {str(e)}"
            )
            self.logger.error(wrapped_error, exc_info=True)
            raise wrapped_error

    @abstractmethod
    def _do_parse(self, file_bytes: bytes, file_name: str, **kwargs) -> Document:
        """
        [Abstract Hook] Implement the actual parsing logic.

        Args:
            file_bytes (bytes): File content.
            file_name (str): Filename.

        Returns:
            Document: The parsed result.
        """
        raise NotImplementedError

    def _process_image_data(
        self,
        image_bytes: bytes,
        img_format: str,
        elem_id: str,
        page_num: int,
        bbox: Optional[BoundingBox] = None,
        ocr_enabled: bool = True,
    ) -> ImageElement:
        """
        Helper to handle image extraction and OCR.

        Args:
            image_bytes (bytes): Raw image data.
            img_format (str): Image format (png, jpg).
            elem_id (str): Unique element ID.
            page_num (int): Page number.
            bbox (BoundingBox, optional): Coordinates.
            ocr_enabled (bool): Whether to attempt OCR.

        Returns:
            ImageElement: Constructed image element, possibly with OCR text.
        """
        import base64

        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        ocr_text = None

        if ocr_enabled and self.ocr_engine:
            try:
                extracted = self.ocr_engine.ocr(image_bytes)
                if extracted and extracted.strip():
                    ocr_text = extracted.strip()
                    self._log(
                        f"OCR extracted {len(ocr_text)} chars from image {elem_id}"
                    )
            except Exception as e:
                self._log(f"OCR failed for image {elem_id}: {e}", level="warning")

        return ImageElement(
            id=elem_id,
            type="image",
            bbox=bbox,
            meta=ElementMetadata(page_num=page_num, id=elem_id),
            image_base64=image_base64,
            image_format=img_format,
            ocr_text=ocr_text,
        )
