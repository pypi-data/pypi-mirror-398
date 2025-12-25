import unittest
from unittest.mock import MagicMock, patch

from sayou.document.interfaces.base_converter import BaseConverter
from sayou.document.interfaces.base_ocr import BaseOCR
from sayou.document.interfaces.base_parser import BaseDocumentParser
from sayou.document.models import Document
from sayou.document.pipeline import DocumentPipeline

# -------------------------------------------------------------------------
# Test Helpers: Mock Classes (Updated __init__)
# -------------------------------------------------------------------------


class MockPdfParser(BaseDocumentParser):
    component_name = "MockPdfParser"

    def __init__(self, ocr_engine=None):
        super().__init__(ocr_engine=ocr_engine)
        self.parse_called_args = None

    @classmethod
    def can_handle(cls, file_bytes: bytes, file_name: str) -> float:
        if file_bytes.startswith(b"%PDF"):
            return 1.0
        return 0.0

    def _do_parse(self, file_bytes: bytes, file_name: str, **kwargs) -> Document:
        self.parse_called_args = kwargs
        return Document(
            file_name=file_name, file_id="test", doc_type="pdf", page_count=1, pages=[]
        )


class MockImageConverter(BaseConverter):
    component_name = "MockImageConverter"
    SUPPORTED_TYPES = [".png"]

    @classmethod
    def can_handle(cls, file_bytes: bytes, file_name: str) -> float:
        if file_bytes.startswith(b"\x89PNG"):
            return 1.0
        return 0.0

    def _do_convert(self, file_bytes: bytes, file_name: str, **kwargs) -> bytes:
        return b"%PDF-converted"


class MockOCR(BaseOCR):
    component_name = "MockOCR"

    @classmethod
    def can_handle(cls, image_bytes: bytes, lang: str = "eng") -> float:
        return 1.0

    def _do_ocr(self, image_bytes: bytes, **kwargs) -> str:
        return "ocr_text"


# -------------------------------------------------------------------------
# Test Case
# -------------------------------------------------------------------------


class TestDocumentPipeline(unittest.TestCase):

    def setUp(self):
        self.pipeline = DocumentPipeline()
        self.pipeline.initialize()

        self.pipeline.parser_cls_map.clear()
        self.pipeline.converter_cls_map.clear()
        self.pipeline.ocr_cls_map.clear()

        self.pipeline.parser_cls_map["mock_pdf"] = MockPdfParser
        self.pipeline.converter_cls_map["mock_img"] = MockImageConverter
        self.pipeline.ocr_cls_map["mock_ocr"] = MockOCR

    def test_score_based_routing(self):
        """Magic Byte 기반 라우팅 테스트"""
        dummy_file = b"%PDF-dummy"
        file_name = "wrong_ext.txt"

        result = self.pipeline.run(dummy_file, file_name)

        self.assertIsNotNone(result)
        self.assertEqual(result.doc_type, "pdf")

    def test_conversion_fallback_logic(self):
        """이미지 -> 컨버터 -> 파서 흐름 테스트"""
        dummy_img = b"\x89PNG-dummy"
        file_name = "test.png"

        result = self.pipeline.run(dummy_img, file_name)

        self.assertIsNotNone(result)
        self.assertEqual(result.doc_type, "pdf")
        self.assertTrue(result.file_name.endswith(".pdf"))

    def test_ocr_injection_and_config_propagation(self):
        """OCR 주입 및 설정 전파 테스트"""
        dummy_file = b"%PDF-ocr"
        file_name = "scan.pdf"

        ocr_config = {"engine_path": "/usr/bin/tesseract", "lang": "kor"}

        with patch.object(
            MockPdfParser,
            "_do_parse",
            side_effect=MockPdfParser._do_parse,
            autospec=True,
        ) as spy_parse:
            self.pipeline.run(dummy_file, file_name, ocr=ocr_config, extra_opt="val")

            args, kwargs = spy_parse.call_args
            self.assertEqual(kwargs.get("engine_path"), "/usr/bin/tesseract")
            self.assertEqual(kwargs.get("lang"), "kor")
            self.assertEqual(kwargs.get("extra_opt"), "val")


if __name__ == "__main__":
    unittest.main()
