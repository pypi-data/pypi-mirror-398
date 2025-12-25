from abc import abstractmethod
from typing import Any, List

from sayou.core.base_component import BaseComponent
from sayou.core.decorators import measure_time
from sayou.core.schemas import SayouBlock

from ..core.exceptions import NormalizationError


class BaseNormalizer(BaseComponent):
    """
    (Tier 1) Abstract base class for converting raw input into SayouBlock.

    Normalizers are responsible for structural transformation:
    Raw Data (JSON, HTML, DB Row) -> List[SayouBlock]
    """

    component_name = "BaseNormalizer"
    SUPPORTED_TYPES = []

    @classmethod
    def can_handle(cls, raw_data: Any, strategy: str = "auto") -> float:
        """
        Determines if this normalizer can handle the raw input data.

        Args:
            raw_data: The input data (dict, str, Document object, etc.)
            strategy: Explicit type hint from user (e.g. 'html', 'json')

        Returns:
            float: Confidence score (0.0 to 1.0)
        """
        return 0.0

    @measure_time
    def normalize(self, raw_data: Any) -> List[SayouBlock]:
        """
        Execute the normalization process.

        Args:
            raw_data: The raw input data from Connector or Document.

        Returns:
            List[SayouBlock]: A list of normalized content blocks.

        Raises:
            NormalizationError: If transformation fails.
        """
        self._emit("on_start", input_data={"type": type(raw_data).__name__})

        self._log(f"Normalizing data (Type: {type(raw_data).__name__})")

        try:
            blocks = self._do_normalize(raw_data)

            self._emit("on_finish", result_data={"blocks": len(blocks)}, success=True)

            if not isinstance(blocks, list):
                raise NormalizationError(f"Output must be a list, got {type(blocks)}")

            return blocks

        except Exception as e:
            self._emit("on_error", error=e)
            wrapped_error = NormalizationError(
                f"[{self.component_name}] Failed: {str(e)}"
            )
            self.logger.error(wrapped_error, exc_info=True)
            raise wrapped_error

    @abstractmethod
    def _do_normalize(self, raw_data: Any) -> List[SayouBlock]:
        """
        [Abstract Hook] Implement logic to convert specific raw format to SayouBlocks.

        Args:
            raw_data: The raw input.

        Returns:
            List[SayouBlock]: The standardized blocks.
        """
        raise NotImplementedError
