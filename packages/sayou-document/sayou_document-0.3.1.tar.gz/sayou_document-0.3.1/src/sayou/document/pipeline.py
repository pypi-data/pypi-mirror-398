import importlib
import pkgutil
from typing import Any, Dict, List, Optional, Type

from sayou.core.base_component import BaseComponent
from sayou.core.decorators import safe_run
from sayou.core.registry import COMPONENT_REGISTRY

from .core.exceptions import ParserError
from .interfaces.base_converter import BaseConverter
from .interfaces.base_ocr import BaseOCR
from .interfaces.base_parser import BaseDocumentParser
from .models import Document


class DocumentPipeline(BaseComponent):
    """
    Orchestrates the document parsing process using a fully dynamic registry system.

    It acts as a pure orchestrator:
    1. Discovers all available plugins (Parsers, OCRs, Converters).
    2. Selects the best components based on 'can_handle' scores.
    3. Injects dependencies (OCR Engine) at runtime if configured.
    """

    component_name = "DocumentPipeline"

    def __init__(
        self,
        extra_converters: Optional[List[Type[BaseConverter]]] = None,
        extra_ocrs: Optional[List[Type[BaseOCR]]] = None,
        extra_parsers: Optional[List[Type[BaseDocumentParser]]] = None,
        **kwargs,
    ):
        """
        Initializes the pipeline without hardcoded dependencies.

        Args:
            extra_converters: List of custom converter classes to register.
            **kwargs: Global configuration (e.g., {'ocr': {'lang': 'kor'}}).
        """
        super().__init__()

        self.converter_cls_map: Dict[str, Type[Any]] = {}
        self.ocr_cls_map: Dict[str, Type[Any]] = {}
        self.parser_cls_map: Dict[str, Type[Any]] = {}

        # 1. Load Defaults
        self._register("sayou.document.converter")
        self._register("sayou.document.ocr")
        self._register("sayou.document.parser")
        self._register("sayou.document.plugins")

        self._load_from_registry()

        # 2. Register Extras
        if extra_converters:
            for cls in extra_converters:
                self._register_manual(cls)

        if extra_ocrs:
            for cls in extra_ocrs:
                self._register_manual(cls)

        if extra_parsers:
            for cls in extra_parsers:
                self._register_manual(cls)

        self.global_config = kwargs

        self.initialize(**kwargs)

    def _register_manual(self, cls):
        """
        Safely registers a user-provided class.
        """
        if not isinstance(cls, type):
            raise TypeError(
                f"Invalid converter: {cls}. "
                f"Please pass the CLASS itself (e.g., MyConverter), not an instance (MyConverter())."
            )

        name = getattr(cls, "component_name", cls.__name__)
        self.converter_cls_map[name] = cls

    @classmethod
    def process(
        cls,
        file_bytes: bytes,
        file_name: str,
        **kwargs,
    ) -> Optional[Document]:
        """
        [Facade] 1-Line Execution Method.
        Creates an instance, runs it, and returns the result immediately.
        """
        instance = cls(**kwargs)
        return instance.run(file_bytes, file_name, **kwargs)

    def _register(self, package_name: str):
        """
        Automatically discovers and registers plugins from the specified package.
        """
        try:
            package = importlib.import_module(package_name)
            if hasattr(package, "__path__"):
                for _, name, _ in pkgutil.iter_modules(package.__path__):
                    full_name = f"{package_name}.{name}"
                    try:
                        importlib.import_module(full_name)
                        self._log(f"Discovered module: {full_name}", level="debug")
                    except Exception as e:
                        self._log(
                            f"Failed to import module {full_name}: {e}", level="warning"
                        )
                        pass
        except ImportError as e:
            self._log(f"Package not found: {package_name} ({e})", level="debug")
            pass

    def _load_from_registry(self):
        """
        Populates local parser map from the global registry.
        """
        if "converter" in COMPONENT_REGISTRY:
            self.converter_cls_map.update(COMPONENT_REGISTRY["converter"])

        if "ocr" in COMPONENT_REGISTRY:
            self.ocr_cls_map.update(COMPONENT_REGISTRY["ocr"])

        if "parser" in COMPONENT_REGISTRY:
            self.parser_cls_map.update(COMPONENT_REGISTRY["parser"])

    @safe_run(default_return=None)
    def initialize(self, **kwargs):
        """
        Initialize all registered parsers, converter, and the OCR engine.
        """
        self.global_config.update(kwargs)
        total_plugins = (
            len(self.converter_cls_map)
            + len(self.ocr_cls_map)
            + len(self.parser_cls_map)
        )
        self._log(f"DocumentPipeline initialized. Loaded Plugins: {total_plugins}")

    def run(
        self,
        file_bytes: bytes,
        file_name: str,
        ocr: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Optional[Document]:
        """
        Executes the parsing pipeline.

        Args:
            file_bytes (bytes): Binary content.
            file_name (str): Original filename.
            ocr (dict, optional): OCR configuration. If provided, OCR is enabled.
                                e.g., {'engine_path': 'C:/...', 'lang': 'kor'}
            **kwargs: Additional runtime options.

        Returns:
            Document: Parsed document object.
        """
        if not file_bytes:
            raise ParserError("Input file bytes are empty.")

        run_config = {**self.global_config, **kwargs}
        if ocr:
            run_config.update(ocr)

        self._emit("on_start", input_data={"filename": file_name})

        # ---------------------------------------------------------------------
        # Phase 1: Component Resolution (Strategy Pattern)
        # ---------------------------------------------------------------------
        # 1-1. Parser Selection
        parser_cls = self._resolve_component(
            self.parser_cls_map,
            primary_input=file_bytes,
            secondary_input=file_name,
            category="Parser",
        )

        # 1-2. Converter Fallback (If no parser found)
        if not parser_cls:
            converter_cls = self._resolve_component(
                self.converter_cls_map,
                primary_input=file_bytes,
                secondary_input=file_name,
                category="Converter",
            )

            if converter_cls:
                self._log(
                    f"No direct parser found. Attempting conversion via {converter_cls.component_name}..."
                )
                converter = converter_cls()
                converter.initialize(**run_config)
                try:
                    converted_bytes = converter.convert(
                        file_bytes, file_name, **run_config
                    )
                    if converted_bytes:
                        file_bytes = converted_bytes
                        file_name = f"{file_name}.pdf"

                        parser_cls = self._resolve_component(
                            self.parser_cls_map,
                            primary_input=file_bytes,
                            secondary_input=file_name,
                            category="Parser (Post-Conversion)",
                        )
                except Exception as e:
                    self._log(f"Conversion warning: {e}", level="warning")

        if not parser_cls:
            error_msg = f"No suitable parser found for {file_name}"
            self._log(f"⚠️ {error_msg}", level="error")
            raise ParserError(error_msg)

        # ---------------------------------------------------------------------
        # Phase 2: OCR Injection (Dependency Injection)
        # ---------------------------------------------------------------------
        ocr_instance = None
        if ocr:
            target_engine = ocr.get("engine_name", "default")
            ocr_cls = self._resolve_component(
                self.ocr_cls_map,
                primary_input=b"",
                secondary_input=target_engine,
                category="OCR Engine",
            )

            if ocr_cls:
                ocr_instance = ocr_cls()
                ocr_instance.initialize(**ocr)
                self._log(f"OCR Engine enabled: {ocr_cls.component_name}")

        # ---------------------------------------------------------------------
        # Phase 3: Execution
        # ---------------------------------------------------------------------
        parser = parser_cls()

        if ocr_instance and hasattr(parser, "set_ocr_engine"):
            parser.set_ocr_engine(ocr_instance)

        parser.initialize(**run_config)
        self._log(f"Routing '{file_name}' to {parser.component_name}...")

        try:
            doc = parser.parse(file_bytes, file_name, **run_config)
            self._emit("on_finish", result_data=doc, success=True)
            return doc
        except Exception as e:
            self._emit("on_error", error=e)
            raise e

    def _resolve_component(
        self,
        cls_map: Dict[str, Type[Any]],
        primary_input: Any,
        secondary_input: Any,
        category: str = "Component",
    ) -> Optional[Type[Any]]:
        """
        Standardized Scoreboard Resolution Logic.
        Selects the best component from the map based on score.

        Args:
            cls_map: Candidate components map.
            primary_input: Main data (e.g., file_bytes).
            secondary_input: Context data (e.g., filename, engine_name).
            category: Label for logging (e.g., "Parser", "OCR").
        """
        best_score = 0.0
        best_cls = None

        info_str = f"Context: {secondary_input}"
        if hasattr(primary_input, "__len__"):
            info_str += f", Len: {len(primary_input)}"

        log_lines = [f"Scoring for {category} ({info_str}):"]

        for cls in set(cls_map.values()):
            try:
                score = cls.can_handle(primary_input, secondary_input)

                mark = ""
                if score > best_score:
                    best_score = score
                    best_cls = cls
                    mark = "👑"

                log_lines.append(f"   - {cls.__name__}: {score} {mark}")

            except Exception as e:
                log_lines.append(f"   - {cls.__name__}: Error ({e})")

        self._log("\n".join(log_lines))

        if best_cls and best_score > 0.1:
            return best_cls

        self._log(
            "⚠️ No suitable component found (Score 0).",
            level="warning",
        )
        return None
