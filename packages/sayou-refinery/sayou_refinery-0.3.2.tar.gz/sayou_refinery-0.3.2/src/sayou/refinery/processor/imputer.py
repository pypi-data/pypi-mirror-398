from typing import Any, Dict, List

from sayou.core.registry import register_component
from sayou.core.schemas import SayouBlock

from ..interfaces.base_processor import BaseProcessor


@register_component("processor")
class Imputer(BaseProcessor):
    """
    (Tier 2) Fills missing values in 'record' type blocks using defined rules.

    Only operates on blocks with type='record' where the content is a dictionary.
    """

    component_name = "Imputer"

    @classmethod
    def can_handle(cls, blocks: list) -> float:
        if super().can_handle(blocks) > 0:
            return 0.8
        return 0.0

    def initialize(self, imputation_rules: Dict[str, Any] = None, **kwargs):
        """
        Set imputation rules.

        Args:
            rules (Dict[str, Any]): Mapping of field names to default values.
                                    Example: {"category": "Unknown", "price": 0.0}
            **kwargs: Additional arguments.
        """
        self.rules = imputation_rules or {}
        if not self.rules:
            self._log("Imputer initialized with no rules.", level="warning")

    def _do_process(self, blocks: List[SayouBlock]) -> List[SayouBlock]:
        """
        Apply imputation rules to record blocks.

        Args:
            blocks (List[SayouBlock]): Input blocks.

        Returns:
            List[SayouBlock]: Blocks with missing values filled.
        """
        for block in blocks:
            if block.type != "record" or not isinstance(block.content, dict):
                continue

            record = block.content

            for field, default_value in self.rules.items():
                if record.get(field) is None:
                    record[field] = default_value

            block.content = record

        return blocks
