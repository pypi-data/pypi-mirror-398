import importlib
import pkgutil
from typing import Any, Dict, List, Optional, Type

from sayou.core.base_component import BaseComponent
from sayou.core.decorators import safe_run
from sayou.core.registry import COMPONENT_REGISTRY

from .core.exceptions import WriterError
from .interfaces.base_writer import BaseWriter


class LoaderPipeline(BaseComponent):
    """
    Orchestrates the data loading process.

    Acts as a router that dispatches the data payload to the appropriate
    writer implementation based on the `strategy` key (e.g., 'file', 'neo4j').
    """

    component_name = "LoaderPipeline"

    def __init__(
        self,
        extra_writers: Optional[List[Type[BaseWriter]]] = None,
        **kwargs,
    ):
        """
        Initialize all registered writers.
        Passes global configuration (e.g., DB connection pools) to writers.

        Args:
            extra_writers: List of custom writer classes to register.
            **kwargs: Global configuration.
        """
        super().__init__()

        self.writers_cls_map: Dict[str, Type[BaseWriter]] = {}

        self._register("sayou.loader.writer")
        self._register("sayou.loader.plugins")

        self._load_from_registry()

        if extra_writers:
            for cls in extra_writers:
                self._register_manual(cls)

        self.global_config = kwargs

        self.initialize(**kwargs)

    def _register_manual(self, cls):
        """
        Safely registers a user-provided class.
        """
        if not isinstance(cls, type):
            raise TypeError(
                f"Invalid writer: {cls}. "
                f"Please pass the CLASS itself (e.g., MyWriter), not an instance (MyWriter())."
            )

        name = getattr(cls, "component_name", cls.__name__)
        self.writers_cls_map[name] = cls

    @classmethod
    def process(
        cls,
        input_data: Any,
        destination: str,
        strategy: str = "auto",
        **kwargs,
    ) -> bool:
        """
        [Facade] One-line execution method.

        Instantiates the pipeline and runs the chunking process immediately.

        Args:
            input_data (Any): The payload to write.
            destination (str): Target location/URI.
            strategy (str): The writer strategy to use (default: 'file').
            **kwargs: Additional writer-specific options (auth, mode).

        Returns:
            bool: True if operation was successful.

        Raises:
            WriterError: If the strategy is unknown or writing fails.
        """
        instance = cls(**kwargs)
        return instance.run(input_data, destination, strategy, **kwargs)

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
        if "writer" in COMPONENT_REGISTRY:
            self.writers_cls_map.update(COMPONENT_REGISTRY["writer"])

    @safe_run(default_return=None)
    def initialize(self, **kwargs):
        """
        Initialize all sub-components (Writers).

        Updates global configuration and logs status.
        Actual component instantiation happens lazily during run().

        Args:
            **kwargs: Updates to the global configuration.
        """
        self.global_config.update(kwargs)

        n_writer = len(self.writers_cls_map)
        self._log(f"LoaderPipeline initialized. Available: {n_writer} Writers")

    def run(
        self,
        input_data: Any,
        destination: str,
        strategy: str = "auto",
        **kwargs,
    ) -> bool:
        """
        Execute the loading strategy.

        Args:
            input_data (Any): The payload to write.
            destination (str): Target location/URI.
            strategy (str): The writer strategy to use (default: 'file').
            **kwargs: Additional writer-specific options (auth, mode).

        Returns:
            bool: True if operation was successful.

        Raises:
            WriterError: If the strategy is unknown or writing fails.
        """
        if not input_data:
            return True

        # 1. Config Merge
        run_config = {**self.global_config, **kwargs}

        self._emit("on_start", input_data={"strategy": strategy})

        # 2. Resolve Writer
        writer_cls = self._resolve_writer(input_data, destination, strategy)

        if not writer_cls:
            error_msg = f"No suitable writer found for strategy='{strategy}'"
            self._emit("on_error", error=Exception(error_msg))
            raise WriterError(error_msg)

        # 3. Instantiate & Initialize (Lazy Loading)
        writer = writer_cls()
        writer.initialize(**run_config)

        self._log(f"Routing to writer: {writer.component_name}")

        try:
            # 4. Execute
            writer.write(input_data, destination)

            self._emit(
                "on_finish", result_data={"destination": destination}, success=True
            )
            return True

        except Exception as e:
            self._emit("on_error", error=e)
            raise e

    def _resolve_writer(
        self,
        raw_data: Any,
        destination: str,
        strategy: str,
    ) -> Optional[Type[BaseWriter]]:
        """
        Selects the best writer based on score or explicit type match.

        Args:
            raw_data (Any): The input data to evaluate.
            strategy (str): The requested strategy name.

        Returns:
            Optional[Type[BaseWriter]]: The selected writer class or None.
        """
        if strategy in self.writers_cls_map:
            return self.writers_cls_map[strategy]

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

        for cls in set(self.writers_cls_map.values()):
            try:
                score = cls.can_handle(raw_data, destination, strategy)

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
            "⚠️ No suitable writer found (Score 0).",
            level="warning",
        )
        return None
