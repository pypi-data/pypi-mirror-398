import importlib
import pkgutil
from typing import Dict, Iterator, List, Optional, Type

from sayou.core.base_component import BaseComponent
from sayou.core.decorators import safe_run
from sayou.core.registry import COMPONENT_REGISTRY
from sayou.core.schemas import SayouPacket, SayouTask

from .interfaces.base_fetcher import BaseFetcher
from .interfaces.base_generator import BaseGenerator


class ConnectorPipeline(BaseComponent):
    """
    Orchestrates the data collection process by connecting Generators and Fetchers.
    """

    component_name = "ConnectorPipeline"

    def __init__(
        self,
        extra_generators: Optional[List[Type[BaseGenerator]]] = None,
        **kwargs,
    ):
        """
        Initializes the pipeline and discovers available components.

        Sets up the internal storage for generators and fetchers, scans specific
        package paths to automatically discover plugins, and loads them from the
        global registry into the local mapping.

        Args:
            extra_generators: List of custom generator classes to register.
            **kwargs: Configuration arguments passed to the parent component.
        """
        super().__init__()

        self.generator_cls_map: Dict[str, Type[BaseGenerator]] = {}
        self.fetcher_cls_map: Dict[str, Type[BaseFetcher]] = {}

        self._register("sayou.connector.generator")
        self._register("sayou.connector.fetcher")
        self._register("sayou.connector.plugins")

        self._load_from_registry()

        if extra_generators:
            for cls in extra_generators:
                self._register_manual(cls)

        self.global_config = kwargs

        self.initialize(**kwargs)

    def _register_manual(self, cls):
        """
        Safely registers a user-provided class.
        """
        if not isinstance(cls, type):
            raise TypeError(
                f"Invalid generator: {cls}. "
                f"Please pass the CLASS itself (e.g., MyGenerator), not an instance (MyGenerator())."
            )

        name = getattr(cls, "component_name", cls.__name__)
        self.generators_cls_map[name] = cls

    @classmethod
    def process(
        cls,
        source: str,
        strategy: str = "auto",
        **kwargs,
    ) -> Iterator[SayouPacket]:
        """
        [Facade] 1-Line Execution Method.
        Creates an instance, runs it, and returns the result immediately.
        """
        instance = cls(**kwargs)
        return instance.run(source, strategy, **kwargs)

    def _register(self, package_name: str):
        """
        Automatically discovers and registers plugins from the specified package.

        Scans the directory of the given package name and attempts to import all
        submodules found. Importing these modules triggers the `@register_component`
        decorator attached to the classes, effectively registering them into the
        global `COMPONENT_REGISTRY`.

        Args:
            package_name (str): The dot-separated Python package path to scan
                                (e.g., "sayou.connector.generator").
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
            self._log(f"Package not found: {package_name} ({e})", level="warning")

    def _load_from_registry(self):
        """
        Populates local component maps from the global registry.

        Iterates through the global `COMPONENT_REGISTRY` to retrieve registered
        generator and fetcher classes. It stores references to these classes in
        `self.generator_cls_map` and instantiates fetchers in `self.fetcher_cls_map`.
        """
        for name, cls in COMPONENT_REGISTRY["generator"].items():
            self.generator_cls_map[name] = cls
            supported = getattr(cls, "SUPPORTED_TYPES", [])
            for t in supported:
                self.generator_cls_map[t] = cls

        for name, cls in COMPONENT_REGISTRY["fetcher"].items():
            instance = cls()
            for t in getattr(instance, "SUPPORTED_TYPES", []):
                self.fetcher_cls_map[t] = instance

    @safe_run(default_return=None)
    def initialize(self, **kwargs):
        """
        Perform global initialization for the pipeline.

        This method is protected by safe_run decorators in the actual implementation
        to prevent initialization crashes.

        Args:
            **kwargs: Global configuration parameters.
        """
        self.global_config.update(kwargs)
        self._log("ConnectorPipeline initialized.")

    def run(
        self,
        source: str,
        strategy: str = "auto",
        **kwargs,
    ) -> Iterator[SayouPacket]:
        """
        Execute the collection pipeline.

        This is the main entry point. It selects a Generator based on the strategy,
        produces Tasks, routes them to the appropriate Fetcher, and yields the results.

        Args:
            source (str): The root source (e.g., file path, URL, connection string).
            strategy (str): The name of the generator strategy to use (default: "auto").
            **kwargs: Additional arguments passed to the Generator's initialize method.

        Yields:
            Iterator[SayouPacket]: A stream of packets containing fetched data.

        Raises:
            ValueError: If the specified strategy is not registered.
        """
        self._emit("on_start", input_data={"source": source, "strategy": strategy})

        # 1. Generator 선택
        generator_cls = self._resolve_generator(source, strategy)
        generator = generator_cls()

        for cb in self._callbacks:
            generator.add_callback(cb)

        # 2. Generator 초기화
        generator.initialize(source=source, **kwargs)
        self._log(f"Connector started using strategy '{strategy}' on '{source}'")

        # 3. Execution Loop
        count = 0
        success_count = 0

        try:
            for task in generator.generate():
                if not isinstance(task, SayouTask):
                    self._log(
                        f"Invalid task type from generator: {type(task)}",
                        level="warning",
                    )
                    continue

                # 4. Fetcher 라우팅
                fetcher = self.fetcher_cls_map.get(task.source_type)
                if not fetcher:
                    self._log(
                        f"Skipping task {task.uri}: No fetcher for type '{task.source_type}'"
                    )
                    continue

                for cb in self._callbacks:
                    fetcher.add_callback(cb)

                # 5. Fetch 수행
                packet = fetcher.fetch(task)

                # 6. 결과 처리
                if packet.success:
                    success_count += 1
                    yield packet
                else:
                    self._log(f"Fetch failed: {packet.error}")

                # 7. Feedback Loop
                generator.feedback(packet)
                count += 1

            self._emit("on_finish", result_data={"count": count}, success=True)

        except Exception as e:
            self._emit("on_error", error=e)
            raise e

        self._log(f"Connector finished. Processed: {count}, Success: {success_count}")

    def _resolve_generator(
        self,
        source: str,
        strategy: str,
    ) -> BaseGenerator:
        """
        Determines the appropriate generator strategy to use.

        Prioritizes the strategy explicitly specified by the user. If the strategy
        is set to 'auto' or None, it attempts to detect the most suitable generator
        based on the source string using the `can_handle` method of registered generators.

        Args:
            source (str): The input source string (e.g., file path, URL, connection string).
            strategy (str): The name of the strategy to use (e.g., 'file', 'sqlite').
                            If 'auto' or None, automatic detection is performed.

        Returns:
            BaseGenerator: The initialized generator instance ready for execution.

        Raises:
            ValueError: If a specific strategy is requested but not found in the registry.
        """
        if strategy and strategy != "auto":
            gen = self.generator_cls_map.get(strategy)
            if not gen:
                raise ValueError(f"Unknown strategy: {strategy}")
            return gen

        best_score = 0.0
        best_cls = None

        log_lines = [
            f"Scoring for Item (Type: {source}):",
            f"Content: {source[:30]}",
        ]

        for cls in set(self.generator_cls_map.values()):
            try:
                score = cls.can_handle(source)

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
            "Auto-detection failed. Falling back to default strategy 'file'.",
            level="warning",
        )
        return self.generator_cls_map["file"]
