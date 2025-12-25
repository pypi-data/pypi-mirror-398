from typing import Any, Dict, List

from sayou.core.registry import register_component
from sayou.core.schemas import SayouBlock

from ..interfaces.base_processor import BaseProcessor


@register_component("processor")
class OutlierHandler(BaseProcessor):
    """
    (Tier 2) Handles numerical outliers in 'record' blocks.

    Can either 'drop' the entire block or 'clamp' the value to a boundary
    if a field violates the defined min/max rules.
    """

    component_name = "OutlierHandler"

    @classmethod
    def can_handle(cls, blocks: list) -> float:
        return 0.8 if super().can_handle(blocks) > 0 else 0.0

    def initialize(self, outlier_rules: Dict[str, Dict[str, Any]] = None, **kwargs):
        """
        Set outlier handling rules.

        Args:
            rules (Dict[str, Dict[str, Any]]): Mapping of field names to constraints.
                Example:
                {
                    "age": {"min": 0, "max": 120, "action": "drop"},
                    "score": {"min": 0, "max": 100, "action": "clamp"}
                }
            **kwargs: Additional arguments.
        """
        self.rules = outlier_rules or {}

    def _do_process(self, blocks: List[SayouBlock]) -> List[SayouBlock]:
        """
        Check numerical fields against rules and filter/modify blocks.

        Args:
            blocks (List[SayouBlock]): Input blocks.

        Returns:
            List[SayouBlock]: Filtered or modified list of blocks.
        """
        valid_blocks = []

        for block in blocks:
            if block.type != "record" or not isinstance(block.content, dict):
                valid_blocks.append(block)
                continue

            record = block.content
            should_drop = False

            for field, rule in self.rules.items():
                val = record.get(field)
                if val is None:
                    continue

                try:
                    val_f = float(val)
                    min_v = rule.get("min")
                    max_v = rule.get("max")
                    action = rule.get("action", "drop")

                    if min_v is not None and val_f < min_v:
                        if action == "drop":
                            should_drop = True
                            break
                        elif action == "clamp":
                            record[field] = min_v

                    if max_v is not None and val_f > max_v:
                        if action == "drop":
                            should_drop = True
                            break
                        elif action == "clamp":
                            record[field] = max_v

                except (ValueError, TypeError):
                    continue

            if not should_drop:
                block.content = record
                valid_blocks.append(block)

        return valid_blocks
