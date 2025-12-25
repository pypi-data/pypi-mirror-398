from abc import abstractmethod
from typing import List

from sayou.core.base_component import BaseComponent
from sayou.core.decorators import measure_time
from sayou.core.schemas import SayouBlock

from ..core.exceptions import ProcessingError


class BaseProcessor(BaseComponent):
    """
    (Tier 1) Abstract base class for processing/cleaning SayouBlock.

    Processors operate on data that is already normalized. They can modify content
    (e.g., PII masking, Imputation) or filter out blocks (e.g., Deduplication).
    """

    component_name = "BaseProcessor"

    @classmethod
    def can_handle(cls, blocks: List[SayouBlock]) -> float:
        """
        Processors are usually explicitly chained, but this allows for
        future smart-selection (e.g., auto-detecting PII).
        """
        if (
            isinstance(blocks, list)
            and len(blocks) > 0
            and isinstance(blocks[0], SayouBlock)
        ):
            return 0.5
        return 0.0

    @measure_time
    def process(self, blocks: List[SayouBlock]) -> List[SayouBlock]:
        """
        Execute the processing logic on a list of blocks.

        Args:
            blocks: Input list of SayouBlocks.

        Returns:
            List[SayouBlock]: Processed list of SayouBlocks.

        Raises:
            ProcessingError: If processing logic fails.
        """
        self._emit("on_start", input_data={"blocks": len(blocks)})
        try:
            if not blocks:
                return []

            result = self._do_process(blocks)

            self._emit("on_finish", result_data={"blocks": len(result)}, success=True)

            return result

        except Exception as e:
            self._emit("on_error", error=e)
            wrapped_error = ProcessingError(f"[{self.component_name}] Failed: {str(e)}")
            self.logger.error(wrapped_error, exc_info=True)
            raise wrapped_error

    @abstractmethod
    def _do_process(self, blocks: List[SayouBlock]) -> List[SayouBlock]:
        """
        [Abstract Hook] Implement cleaning/filtering logic.

        Args:
            blocks: List of input SayouBlocks.

        Returns:
            List[SayouBlock]: Modified list of SayouBlocks.
        """
        raise NotImplementedError
