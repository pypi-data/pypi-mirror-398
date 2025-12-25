from abc import abstractmethod

from sayou.core.base_component import BaseComponent
from sayou.core.decorators import measure_time


class BaseOCR(BaseComponent):
    """
    (Tier 1) Abstract base class for OCR engines.
    """

    component_name = "BaseOCR"

    @classmethod
    def can_handle(cls, image_bytes: bytes, lang: str = "eng") -> float:
        """
        Determines if the OCR engine can handle the image/language.

        Args:
            image_bytes (bytes): Image content.
            lang (str): Language code.

        Returns:
            float: Confidence score.
        """
        return 0.5

    @measure_time
    def ocr(self, image_bytes: bytes, **kwargs) -> str:
        """
        Execute OCR on image bytes.

        Args:
            image_bytes (bytes): Image content.

        Returns:
            str: Extracted text.
        """
        if not image_bytes:
            return ""

        self._emit(
            "on_start",
            input_data={"image_size": len(image_bytes), "engine": self.component_name},
        )

        try:
            text = self._do_ocr(image_bytes, **kwargs)
            clean_text = text.strip() if text else ""
            self._emit(
                "on_finish", result_data={"text_len": len(clean_text)}, success=True
            )
            return clean_text
        except Exception as e:
            self._emit("on_error", error=e)
            self._log(f"OCR execution failed: {e}", level="warning")
            return ""

    @abstractmethod
    def _do_ocr(self, image_bytes: bytes, **kwargs) -> str:
        """
        [Abstract Hook] Implement the actual OCR API call.
        """
        raise NotImplementedError
