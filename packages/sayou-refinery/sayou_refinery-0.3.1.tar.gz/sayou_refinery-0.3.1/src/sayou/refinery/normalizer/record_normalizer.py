from typing import Any, Dict, List

from sayou.core.registry import register_component
from sayou.core.schemas import SayouBlock

from ..core.exceptions import NormalizationError
from ..interfaces.base_normalizer import BaseNormalizer


@register_component("normalizer")
class RecordNormalizer(BaseNormalizer):
    """
    (Tier 2) Converts structured data (Dict/List) into 'record' SayouBlocks.

    Suitable for processing database rows, CSV records, or JSON API responses.
    Each dictionary becomes a separate SayouBlock of type 'record'.
    """

    component_name = "RecordNormalizer"
    SUPPORTED_TYPES = ["json", "dict", "db_row", "record"]

    @classmethod
    def can_handle(cls, raw_data: Any, strategy: str = "auto") -> float:
        if strategy in ["json", "record", "db", "dict"]:
            return 1.0

        if isinstance(raw_data, dict):
            return 0.9
        if isinstance(raw_data, list):
            if len(raw_data) > 0 and isinstance(raw_data[0], dict):
                return 0.9
            return 0.1

        return 0.0

    def _do_normalize(self, raw_data: Any) -> List[SayouBlock]:
        """
        Convert dict or list of dicts into record blocks.

        Args:
            raw_data (Any): A Dictionary or a List of Dictionaries.

        Returns:
            List[SayouBlock]: Blocks of type 'record'.
        """
        blocks = []

        # Case 1: Single Dictionary
        if isinstance(raw_data, dict):
            blocks.append(self._create_block(raw_data))

        # Case 2: List of Dictionaries
        elif isinstance(raw_data, list):
            for item in raw_data:
                if isinstance(item, dict):
                    blocks.append(self._create_block(item))
                else:
                    self._log(
                        f"Skipping non-dict item in list: {type(item)}", level="warning"
                    )

        else:
            raise NormalizationError(
                f"Input must be Dict or List[Dict], got {type(raw_data)}"
            )

        return blocks

    def _create_block(self, data: Dict[str, Any]) -> SayouBlock:
        """
        Helper to wrap a single dictionary into a SayouBlock.

        Args:
            data (Dict[str, Any]): The data record.

        Returns:
            SayouBlock: A block with type='record' and content=data.
        """
        return SayouBlock(
            type="record",
            content=data,
            metadata={"fields": list(data.keys())},
        )
