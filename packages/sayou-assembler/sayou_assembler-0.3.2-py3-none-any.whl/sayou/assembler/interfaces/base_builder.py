from abc import abstractmethod
from typing import Any, Dict, Union

from sayou.core.base_component import BaseComponent
from sayou.core.decorators import measure_time
from sayou.core.schemas import SayouOutput

from ..core.exceptions import BuildError


class BaseBuilder(BaseComponent):
    """
    (Tier 1) Abstract base class for assembling SayouNodes into target formats.

    Implements the Template Method pattern:
    1. `build()`: Validates input, converts Dict to Pydantic Model if needed.
    2. `_do_build()`: Abstract hook for the specific transformation logic.
    """

    component_name = "BaseBuilder"
    SUPPORTED_TYPES = []

    @classmethod
    def can_handle(cls, input_data: Any, strategy: str = "auto") -> float:
        return 0.0

    @measure_time
    def build(self, input_data: Union[SayouOutput, Dict]) -> Any:
        """
        [Template Method] Execute the building process.

        Args:
            input_data (Union[SayouOutput, Dict]): Standardized node data.

        Returns:
            Any: The assembled payload.

        Raises:
            BuildError: If input is invalid or building fails.
        """
        self._emit("on_start", input_data={"strategy": self.component_name})
        self._log(f"Building data with {self.component_name}")

        # Input Normalization
        if isinstance(input_data, dict):
            try:
                # 딕셔너리가 들어오면 Pydantic 모델로 변환하여 검증
                sayou_output = SayouOutput(**input_data)
            except Exception as e:
                raise BuildError(f"Invalid input format: {e}")
        elif isinstance(input_data, SayouOutput):
            sayou_output = input_data
        else:
            raise BuildError(f"Unsupported input type: {type(input_data)}")

        try:
            output = self._do_build(sayou_output)

            self._emit("on_finish", result_data={"output": output}, success=True)
            return output
        except Exception as e:
            self._emit("on_error", error=e)
            self.logger.error(f"Build failed: {e}", exc_info=True)
            raise BuildError(f"[{self.component_name}] Failed: {str(e)}")

    @abstractmethod
    def _do_build(self, data: SayouOutput) -> Any:
        """
        [Abstract Hook] Implement the transformation logic.

        Args:
            data (SayouOutput): Validated input data.

        Returns:
            Any: Target format payload.
        """
        raise NotImplementedError
