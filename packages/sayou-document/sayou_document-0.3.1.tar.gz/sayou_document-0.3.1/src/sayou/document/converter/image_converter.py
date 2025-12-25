import io

try:
    from PIL import Image
except ImportError:
    Image = None

from sayou.core.registry import register_component

from ..core.exceptions import ConversionError
from ..interfaces.base_converter import BaseConverter


@register_component("converter")
class ImageToPdfConverter(BaseConverter):
    """
    (Tier 2) Simple converter that turns Image files (JPG, PNG) into PDF bytes.
    Useful for unifying the pipeline input to PDF format.
    """

    component_name = "ImageToPdfConverter"
    SUPPORTED_TYPES = [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]

    @classmethod
    def can_handle(cls, file_bytes: bytes, file_name: str) -> float:
        """
        Detects image formats via Magic Bytes.
        """
        # 1. Magic Bytes Check
        if file_bytes.startswith(b"\xff\xd8\xff"):
            return 1.0  # JPG
        if file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            return 1.0  # PNG
        if file_bytes.startswith(b"BM"):
            return 1.0  # BMP
        if file_bytes.startswith(b"II*\x00") or file_bytes.startswith(b"MM\x00*"):
            return 1.0  # TIFF

        # 2. Extension Check (Fallback)
        if any(file_name.lower().endswith(ext) for ext in cls.SUPPORTED_TYPES):
            return 0.8

        return 0.0

    def _do_convert(self, file_bytes: bytes, file_name: str, **kwargs) -> bytes:
        if not Image:
            raise ImportError("Pillow is required for ImageToPdfConverter.")

        try:
            image = Image.open(io.BytesIO(file_bytes))

            # PDF 저장을 위해 RGB 모드로 변환 (PNG 투명도 이슈 방지)
            if image.mode in ("RGBA", "LA"):
                background = Image.new("RGB", image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1])
                image = background
            elif image.mode != "RGB":
                image = image.convert("RGB")

            output_buffer = io.BytesIO()
            image.save(output_buffer, format="PDF", resolution=100.0)
            return output_buffer.getvalue()

        except Exception as e:
            raise ConversionError(f"Image conversion failed: {e}")
