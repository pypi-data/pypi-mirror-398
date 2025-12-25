from abc import abstractmethod
from typing import Any, List

from sayou.core.base_component import BaseComponent
from sayou.core.decorators import measure_time
from sayou.core.schemas import SayouOutput

from ..core.exceptions import AdaptationError


class BaseAdapter(BaseComponent):
    """
    (Tier 1) Abstract base class for converting external data into Sayou Standard Schema.

    Implements the Template Method pattern:
    1. `adapt()`: Handles logging, timing, and error wrapping.
    2. `_do_adapt()`: Abstract hook for the specific mapping logic.
    """

    component_name = "BaseAdapter"
    SUPPORTED_TYPES: List[str] = []

    @classmethod
    def can_handle(cls, input_data: Any, strategy: str = "auto") -> float:
        return 0.0

    @measure_time
    def adapt(self, input_data: Any) -> SayouOutput:
        """
        [Template Method] Execute the adaptation process.

        Args:
            input_data (Any): Raw input data (Chunks, Dicts, etc.).

        Returns:
            SayouOutput: The standardized output containing nodes and metadata.

        Raises:
            AdaptationError: If the adaptation logic fails.
        """
        self._log(f"Adapting data (Type: {type(input_data).__name__})")
        self._emit("on_start", input_data={"strategy": self.component_name})

        try:
            output = self._do_adapt(input_data)

            self._emit("on_finish", result_data={"output": output}, success=True)
            self._log(f"Adaptation complete. Generated {len(output.nodes)} nodes.")
            return output

        except Exception as e:
            self._emit("on_error", error=e)
            self.logger.error(f"Adaptation failed: {e}", exc_info=True)
            raise AdaptationError(f"[{self.component_name}] {str(e)}")

    @abstractmethod
    def _do_adapt(self, input_data: Any) -> SayouOutput:
        """
        [Abstract Hook] Implement the mapping logic to create SayouNodes.

        Args:
            input_data (Any): Input data.

        Returns:
            SayouOutput: The constructed output object.
        """
        raise NotImplementedError
