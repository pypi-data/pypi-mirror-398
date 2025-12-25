try:
    import io

    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None

from sayou.core.registry import register_component

from ..core.exceptions import OCRError
from ..interfaces.base_ocr import BaseOCR


@register_component("ocr")
class TesseractOCR(BaseOCR):
    """
    (Tier 2) OCR implementation using Google's Tesseract engine via 'pytesseract'.
    """

    component_name = "TesseractOCR"

    @classmethod
    def can_handle(cls, image_bytes: bytes, lang: str = "eng") -> float:
        """
        Tesseract is a general-purpose OCR engine.
        Returns a moderate confidence score to allow specialized engines to override it.
        """
        # TODO: 'HandwritingOCR' == 0.9
        return 0.5

    def initialize(self, lang: str = "eng+kor", **kwargs):
        """
        Args:
            lang (str): Language code string (e.g., 'eng', 'kor', 'eng+kor').
            **kwargs: Additional options.
        """
        self.lang = lang
        self.default_path = kwargs.get("engine_path") or kwargs.get("tesseract_path")

    def _do_ocr(self, image_bytes: bytes, **kwargs) -> str:
        """
        Performs OCR on image bytes.

        Args:
            image_bytes (bytes): Binary image data.
            **kwargs: Must contain 'engine_path' if not in PATH.

        Returns:
            str: Extracted text.
        """
        if not pytesseract:
            raise ImportError("pytesseract and Pillow are required for TesseractOCR.")

        run_path = kwargs.get("engine_path") or kwargs.get("tesseract_path")
        target_path = run_path or getattr(self, "default_path", None)

        if target_path:
            pytesseract.pytesseract.tesseract_cmd = target_path

        try:
            image = Image.open(io.BytesIO(image_bytes))
            text = pytesseract.image_to_string(image, lang=self.lang)
            return text
        except Exception as e:
            raise OCRError(f"Tesseract execution failed: {e}")
