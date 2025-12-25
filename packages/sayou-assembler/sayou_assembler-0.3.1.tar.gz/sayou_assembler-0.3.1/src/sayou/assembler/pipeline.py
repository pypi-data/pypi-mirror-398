import importlib
import pkgutil
from typing import Any, Dict, List, Optional, Type

from sayou.core.base_component import BaseComponent
from sayou.core.decorators import safe_run
from sayou.core.registry import COMPONENT_REGISTRY

from .core.exceptions import BuildError
from .interfaces.base_builder import BaseBuilder


class AssemblerPipeline(BaseComponent):
    """
    Orchestrates the assembly process.

    This pipeline acts as a factory, routing standardized `SayouOutput` (Nodes)
    to specific builders to generate database-ready payloads (Graph Dicts,
    Vector Lists, or Query Strings).
    """

    component_name = "AssemblerPipeline"

    def __init__(
        self,
        extra_builders: Optional[List[Type[BaseBuilder]]] = None,
        **kwargs,
    ):
        """
        Initialize the pipeline with default and custom builders.

        Args:
            extra_builders: List of custom builders CLASSES (not instances).
            **kwargs: Global configuration.
        """
        super().__init__()

        self.builders_cls_map: Dict[str, Type[BaseBuilder]] = {}

        self._register("sayou.assembler.builder")
        self._register("sayou.assembler.plugins")

        self._load_from_registry()

        if extra_builders:
            for cls in extra_builders:
                self._register_manual(cls)

        self.global_config = kwargs

        self.initialize(**kwargs)

    def _register_manual(self, cls):
        """
        Safely registers a user-provided class.
        """
        if not isinstance(cls, type):
            raise TypeError(
                f"Invalid assembler: {cls}. "
                f"Please pass the CLASS itself (e.g., MyAssembler), not an instance (MyAssembler())."
            )

        name = getattr(cls, "component_name", cls.__name__)
        self.builders_cls_map[name] = cls

    @classmethod
    def process(
        cls,
        input_data: Any,
        strategy: str = "auto",
        **kwargs,
    ) -> Any:
        """
        [Facade] One-line execution method.

        Args:
            input_data (Any):
            strategy (str):
            **kwargs:

        Returns:
            Any:
        """
        instance = cls(**kwargs)
        return instance.run(input_data, strategy, **kwargs)

    def _register(self, package_name: str):
        """
        Automatically discovers and registers plugins from the specified package.

        Args:
            package_name (str): The dot-separated package path.
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
        if "builder" in COMPONENT_REGISTRY:
            self.builders_cls_map.update(COMPONENT_REGISTRY["builder"])

    @safe_run(default_return=None)
    def initialize(self, **kwargs):
        """
        Initialize all sub-components (Builders).

        Updates global configuration and logs status.
        Actual component instantiation happens lazily during run().

        Args:
            **kwargs: Updates to the global configuration.
        """
        self.global_config.update(kwargs)

        n_builder = len(self.builders_cls_map)
        self._log(f"AssemblerPipeline initialized. Available: {n_builder} Builders")

    def run(
        self,
        input_data: Any,
        strategy: str = "auto",
        **kwargs,
    ) -> Any:
        """ """
        if not input_data:
            return []

        # 1. Config Merge
        run_config = {**self.global_config, **kwargs}

        self._emit("on_start", input_data={"strategy": strategy})

        # 2. Resolve Builder
        builder_cls = self._resolve_builder(input_data, strategy)

        if not builder_cls:
            error_msg = f"No suitable builder found for strategy='{strategy}'"
            self._emit("on_error", error=Exception(error_msg))
            raise BuildError(error_msg)

        # 3. Instantiate & Initialize (Lazy Loading)
        builder = builder_cls()
        builder.initialize(**run_config)

        self._log(f"Routing to builder: {builder.component_name}")

        try:
            # 4. Execute
            chunks = builder.build(input_data)

            self._emit(
                "on_finish", result_data={"chunks_count": len(chunks)}, success=True
            )
            return chunks

        except Exception as e:
            self._emit("on_error", error=e)
            raise e

    def _resolve_builder(
        self,
        raw_data: Any,
        strategy: str,
    ) -> Optional[Type[BaseBuilder]]:
        """
        Selects the best splitter based on score or explicit type match.

        Args:
            raw_data (Any): The input data to evaluate.
            strategy (str): The requested strategy name.

        Returns:
            Optional[Type[BaseBuilder]]: The selected splitter class or None.
        """
        if strategy in self.builders_cls_map:
            return self.builders_cls_map[strategy]

        best_score = 0.0
        best_cls = None

        log_lines = [
            f"Scoring for Item (Type: {raw_data.type}, Len: {len(raw_data.content)}):",
            f"Content: {raw_data.content[:30]}",
        ]

        for cls in set(self.builders_cls_map.values()):
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
            "⚠️ No suitable builder found (Score 0).",
            level="warning",
        )

        return None
