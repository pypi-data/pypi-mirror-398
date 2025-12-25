import importlib
import pkgutil
from typing import Any, Dict, List, Optional, Type

from sayou.core.base_component import BaseComponent
from sayou.core.decorators import safe_run
from sayou.core.registry import COMPONENT_REGISTRY
from sayou.core.schemas import SayouOutput

from .core.exceptions import AdaptationError
from .interfaces.base_adapter import BaseAdapter


class WrapperPipeline(BaseComponent):
    """
    Orchestrates the data wrapping process.

    This pipeline acts as the final gateway before data storage. It receives
    processed data (usually chunks) and delegates it to a specific `Adapter`
    to convert it into the standard `SayouNode` format.
    """

    component_name = "WrapperPipeline"

    def __init__(
        self,
        extra_adapters: Optional[List[Type[BaseAdapter]]] = None,
        **kwargs,
    ):
        """
        Initialize the pipeline with default and optional custom adapters.

        Args:
            extra_adapters: Custom adapters to register.
            **kwargs: Global configuration.
        """
        super().__init__()

        self.adapters_cls_map: Dict[str, Type[BaseAdapter]] = {}

        self._register("sayou.wrapper.adapter")
        self._register("sayou.wrapper.plugins")

        self._load_from_registry()

        if extra_adapters:
            for cls in extra_adapters:
                self._register_manual(cls)

        self.global_config = kwargs

        self.initialize(**kwargs)

    def _register_manual(self, cls):
        """
        Safely registers a user-provided class.
        """
        if not isinstance(cls, type):
            raise TypeError(
                f"Invalid adapter: {cls}. "
                f"Please pass the CLASS itself (e.g., MyAdapter), not an instance (MyAdapter())."
            )

        name = getattr(cls, "component_name", cls.__name__)
        self.adapters_cls_map[name] = cls

    @classmethod
    def process(
        cls,
        input_data: Any,
        strategy: str = "auto",
        **kwargs,
    ) -> SayouOutput:
        """
        [Facade] One-line execution method.

        Instantiates the pipeline and executes the wrapping strategy immediately.

        Args:
            input_data (Any): The raw input data to be wrapped.
                Typically a List[SayouChunk] from the ChunkingPipeline,
                or a raw dictionary/list representing the content.
            strategy (str): The explicit adapter strategy to use (default: 'auto').
                If set to 'auto', the pipeline attempts to detect the best adapter
                based on the input data structure.
            **kwargs: Additional configuration options passed to the pipeline
                initialization and the adapter's execution context.

        Returns:
            SayouOutput: A standardized container holding the graph of nodes
                and associated metadata ready for the Assembler/Loader.
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
        if "adapter" in COMPONENT_REGISTRY:
            self.adapters_cls_map.update(COMPONENT_REGISTRY["adapter"])

    @safe_run(default_return=None)
    def initialize(self, **kwargs):
        """
        Initialize all registered adapters.

        Propagates global configuration to all adapters, although adapters
        are typically stateless.

        Args:
            **kwargs: Updates to the global configuration.
        """
        self.global_config.update(kwargs)

        n_adap = len(self.adapters_cls_map)
        self._log(f"WrapperPipeline initialized. Strategies: {n_adap} Adapters")

    def run(
        self,
        input_data: Any,
        strategy: str = "auto",
        **kwargs,
    ) -> SayouOutput:
        """
        Execute the wrapping strategy.

        Args:
            input_data (Any): The input data (e.g., List[Chunk] or raw Dict).
            strategy (str): The adapter strategy to use (default: 'auto').
            **kwargs: Additional keyword arguments to pass to the adapter.

        Returns:
            SayouOutput: A container holding the list of standardized SayouNodes.

        Raises:
            AdaptationError: If the strategy is unknown or execution fails.
        """
        if not input_data:
            return SayouOutput(nodes=[])

        # 1. Config Merge
        run_config = {**self.global_config, **kwargs}

        self._emit("on_start", input_data={"strategy": strategy})

        # 2. Resolve Adapter
        adapter_cls = self._resolve_adapter(input_data, strategy)

        if not adapter_cls:
            error_msg = f"No suitable adapter found for strategy='{strategy}'"
            self._emit("on_error", error=Exception(error_msg))
            raise AdaptationError(error_msg)

        # 3. Instantiate & Initialize (Lazy Loading)
        adapter = adapter_cls()
        adapter.initialize(**run_config)

        self._log(f"Routing to adapter: {adapter.component_name}")

        try:
            # 4. Execute
            output = adapter.adapt(input_data)

            self._emit("on_finish", result_data={"output": output}, success=True)
            return output

        except Exception as e:
            self._emit("on_error", error=e)
            raise e

    def _resolve_adapter(
        self,
        raw_data: Any,
        strategy: str,
    ) -> Optional[Type[BaseAdapter]]:
        """
        Selects the best adapter based on score or explicit type match.

        Args:
            raw_data (Any): The input data to evaluate.
            strategy (str): The requested strategy name.

        Returns:
            Optional[Type[BaseAdapter]]: The selected adapter class or None.
        """
        if strategy in self.adapters_cls_map:
            return self.adapters_cls_map[strategy]

        best_score = 0.0
        best_cls = None

        log_lines = [
            f"Scoring for Item (Type: {raw_data.type}, Len: {len(raw_data.content)}):",
            f"Content: {raw_data.content[:30]}",
        ]

        for cls in set(self.adapters_cls_map.values()):
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
            "⚠️ No suitable adapter found (Score 0)",
            level="warning",
        )

        return None
