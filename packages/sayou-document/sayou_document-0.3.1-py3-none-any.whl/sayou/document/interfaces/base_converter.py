from abc import abstractmethod
from typing import List

from sayou.core.base_component import BaseComponent
from sayou.core.decorators import measure_time

from ..core.exceptions import ConversionError


class BaseConverter(BaseComponent):
    """
    (Tier 1) Abstract base class for file format converters.
    """

    component_name = "BaseConverter"
    SUPPORTED_TYPES: List[str] = []

    @classmethod
    def can_handle(cls, file_bytes: bytes, file_name: str) -> float:
        """
        Determines if this converter handles the given file.

        Args:
            file_bytes (bytes): File content header.
            file_name (str): Filename with extension.

        Returns:
            float: Confidence score (0.0 - 1.0).
        """
        for ext in cls.SUPPORTED_TYPES:
            if file_name.lower().endswith(ext):
                return 1.0
        return 0.0

    @measure_time
    def convert(self, file_bytes: bytes, file_name: str, **kwargs) -> bytes:
        """
        Convert file to a target format.

        Args:
            file_bytes (bytes): Original file content.
            file_name (str): Original filename.

        Returns:
            bytes: Converted file content.

        Raises:
            ConversionError: If conversion fails.
        """
        self._emit(
            "on_start",
            input_data={"filename": file_name, "converter": self.component_name},
        )
        self._log(f"Converting file: {file_name}...")
        try:
            converted_bytes = self._do_convert(file_bytes, file_name, **kwargs)

            if not converted_bytes:
                raise ConversionError("Converter returned empty bytes.")

            self._log(f"Conversion successful. ({len(converted_bytes)} bytes)")
            self._emit(
                "on_finish", result_data={"size": len(converted_bytes)}, success=True
            )
            return converted_bytes

        except Exception as e:
            self._emit("on_error", error=e)
            wrapped_error = ConversionError(
                f"[{self.component_name}] Failed to convert {file_name}: {str(e)}"
            )
            self.logger.error(wrapped_error, exc_info=True)
            return None

    @abstractmethod
    def _do_convert(self, file_bytes: bytes, file_name: str, **kwargs) -> bytes:
        """
        [Abstract Hook] Implement conversion logic.
        """
        raise NotImplementedError
