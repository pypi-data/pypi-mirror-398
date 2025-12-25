import importlib
import pkgutil
from typing import Any, Dict, List, Optional, Type

from sayou.core.base_component import BaseComponent
from sayou.core.decorators import safe_run
from sayou.core.registry import COMPONENT_REGISTRY
from sayou.core.schemas import SayouBlock

from .core.exceptions import RefineryError
from .interfaces.base_normalizer import BaseNormalizer
from .interfaces.base_processor import BaseProcessor


class RefineryPipeline(BaseComponent):
    """
    Orchestrates the data refinement process via dynamic registry.

    Workflow:
    1. Normalization: Converts raw input (Document, HTML, JSON) into standard SayouBlocks.
    2. Processing: Applies a chain of processors (Cleaning, Masking, Dedup) to the blocks.
    """

    component_name = "RefineryPipeline"

    def __init__(
        self,
        extra_normalizers: Optional[List[Type[BaseNormalizer]]] = None,
        **kwargs,
    ):
        """
        Initializes the pipeline and discovers available plugins.

        Args:
            extra_normalizers: Optional list of custom normalizer classes to register.
            **kwargs: Global configuration passed down to components.
                    e.g., processors=["cleaner", "pii_masker"]
        """
        super().__init__()

        self.normalizer_cls_map: Dict[str, Type[BaseNormalizer]] = {}
        self.processor_cls_map: Dict[str, Type[BaseProcessor]] = {}

        self._register("sayou.refinery.normalizer")
        self._register("sayou.refinery.processor")
        self._register("sayou.refinery.plugins")

        self._load_from_registry()

        if extra_normalizers:
            for cls in extra_normalizers:
                self._register_manual(cls)

        self.global_config = kwargs

        self.initialize(**kwargs)

    def _register_manual(self, cls):
        """
        Safely registers a user-provided class.
        """
        if not isinstance(cls, type):
            raise TypeError(
                f"Invalid normalizer: {cls}. "
                f"Please pass the CLASS itself (e.g., MyNormalizer), not an instance (MyNormalizer())."
            )

        name = getattr(cls, "component_name", cls.__name__)
        self.normalizer_cls_map[name] = cls

    @classmethod
    def process(
        cls,
        raw_data: Any,
        strategy: str = "auto",
        processors: List[str] = None,
        **kwargs,
    ) -> List[SayouBlock]:
        """
        [Facade] One-line execution method.

        Args:
            raw_data (Any): Input data to refine.
            strategy (str): Hint for normalizer selection (default: 'auto').
            **kwargs: Configuration options.

        Returns:
            List[SayouBlock]: Refined data blocks.
        """
        instance = cls(**kwargs)
        return instance.run(raw_data, strategy, processors, **kwargs)

    def _register(self, package_name: str):
        """
        Automatically discovers and registers plugins from the specified package.

        Args:
            package_name (str): The dot-separated package path (e.g., 'sayou.refinery.plugins').
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
        except ImportError as e:
            self._log(f"Package not found: {package_name} ({e})", level="debug")

    def _load_from_registry(self):
        """
        Populates local component maps from the global registry.
        """
        if "normalizer" in COMPONENT_REGISTRY:
            self.normalizer_cls_map.update(COMPONENT_REGISTRY["normalizer"])

        if "processor" in COMPONENT_REGISTRY:
            self.processor_cls_map.update(COMPONENT_REGISTRY["processor"])

    @safe_run(default_return=None)
    def initialize(self, **kwargs):
        """
        Initialize all sub-components (Normalizers and Processors).
        Passes global configuration (like PII masking rules) down to components.
        """
        """
        Updates global configuration and logs status.
        Actual component instantiation happens lazily during run().
        
        Args:
            **kwargs: Updates to the global configuration.
        """
        self.global_config.update(kwargs)

        n_norm = len(self.normalizer_cls_map)
        n_proc = len(self.processor_cls_map)
        self._log(
            f"RefineryPipeline initialized. Available: {n_norm} Normalizers, {n_proc} Processors."
        )

    def run(
        self,
        raw_data: Any,
        strategy: str = "auto",
        processors: Optional[List[str]] = None,
        **kwargs,
    ) -> List[SayouBlock]:
        """
        Executes the refinement pipeline: Normalize -> Process Chain.

        Args:
            raw_data (Any): Input data (Document object, dict, string, etc.).
            strategy (str): Hint for normalizer (default: 'auto').
            processors (List[str], optional): List of processor names to execute in order.
                                            If None, executes all registered processors (or a default set).
            **kwargs: Runtime configuration.

        Returns:
            List[SayouBlock]: A list of clean, normalized blocks.
        """
        if raw_data is None:
            return []

        run_config = {**self.global_config, **kwargs}

        self._emit("on_start", input_data={"strategy": strategy})

        # ---------------------------------------------------------
        # Step 1: Normalize (Smart Routing)
        # ---------------------------------------------------------
        normalizer_cls = self._resolve_normalizer(raw_data, strategy)

        if not normalizer_cls:
            error_msg = f"No suitable normalizer found for strategy='{strategy}'"
            self._emit("on_error", error=Exception(error_msg))
            raise RefineryError(error_msg)

        # Instantiate Normalizer
        normalizer = normalizer_cls()

        if hasattr(self, "_callbacks"):
            for cb in self._callbacks:
                normalizer.add_callback(cb)

        normalizer.initialize(**run_config)

        try:
            self._log(f"Normalizing with {normalizer.component_name}...")
            blocks = normalizer.normalize(raw_data)
        except Exception as e:
            self._emit("on_error", error=e)
            self._log(f"Normalization failed: {e}", level="error")
            return []

        # ---------------------------------------------------------
        # Step 2: Process Chain (Dynamic Execution)
        # ---------------------------------------------------------
        chain_names = (
            processors if processors is not None else run_config.get("processors", [])
        )

        if not chain_names and not processors:
            chain_names = []

        active_processors = []

        for name in chain_names:
            proc_cls = self._resolve_processor_by_name(name)
            if proc_cls:
                proc = proc_cls()
                proc.initialize(**run_config)
                active_processors.append(proc)
            else:
                self._log(f"Processor '{name}' not found in registry.", level="warning")

        for proc in active_processors:
            try:
                self._log(f"Running Processor: {proc.component_name}")
                blocks = proc.process(blocks)
            except Exception as e:
                self._log(f"Processor {proc.component_name} failed: {e}", level="error")

        self._emit("on_finish", result_data={"blocks_count": len(blocks)}, success=True)
        return blocks

    def _resolve_normalizer(
        self,
        raw_data: Any,
        strategy: str,
    ) -> Optional[Type[BaseNormalizer]]:
        """
        Selects the best normalizer based on score or explicit type match.
        """
        if strategy in self.normalizer_cls_map:
            return self.normalizer_cls_map[strategy]

        best_score = 0.0
        best_cls = None

        obj_type = getattr(raw_data, "type", type(raw_data).__name__)
        content_len = 0
        if hasattr(raw_data, "content"):
            c = raw_data.content
            if hasattr(c, "__len__"):
                content_len = len(c)
        elif isinstance(raw_data, (str, bytes, list, dict)):
            content_len = len(raw_data)

        log_lines = [f"Scoring for Item (Type: {obj_type}, Len: {content_len}):"]
        if hasattr(raw_data, "content") and isinstance(raw_data.content, str):
            log_lines.append(f"Content Preview: {raw_data.content[:50]}...")
        elif isinstance(raw_data, str):
            log_lines.append(f"Content Preview: {raw_data[:50]}...")

        for cls in set(self.normalizer_cls_map.values()):
            try:
                score = cls.can_handle(raw_data, strategy)

                mark = ""
                if score > best_score:
                    best_score = score
                    best_cls = cls
                    mark = "👑"

                log_lines.append(f"   - {cls.__name__}: {score} {mark}")

            except Exception as e:
                log_lines.append(f"   - {cls.__name__}: Error ({e})")

        self._log("\n".join(log_lines))

        if best_cls and best_score > 0.0:
            return best_cls

        self._log(
            "⚠️ No suitable normalizer found (Score 0).",
            level="warning",
        )
        return None

    def _resolve_processor_by_name(self, name: str) -> Optional[Type[BaseProcessor]]:
        """
        Finds a processor class by its component_name or registry key.
        """
        # 1. Exact Key Match
        if name in self.processor_cls_map:
            return self.processor_cls_map[name]

        # 2. Component Name Match (Loop search)
        for cls in self.processor_cls_map.values():
            if getattr(cls, "component_name", "") == name:
                return cls

        return None
