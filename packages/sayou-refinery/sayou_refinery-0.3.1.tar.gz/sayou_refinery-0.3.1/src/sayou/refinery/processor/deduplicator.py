import json
from typing import List, Set

from sayou.core.registry import register_component
from sayou.core.schemas import SayouBlock

from ..interfaces.base_processor import BaseProcessor


@register_component("processor")
class Deduplicator(BaseProcessor):
    """
    (Tier 2) Removes duplicate blocks based on content hashing.

    It computes a hash of the content for each block and filters out
    subsequent blocks that match an already seen hash.
    """

    component_name = "Deduplicator"

    @classmethod
    def can_handle(cls, blocks: list) -> float:
        if isinstance(blocks, list) and len(blocks) > 1:
            return 1.0
        return 0.0

    def _do_process(self, blocks: List[SayouBlock]) -> List[SayouBlock]:
        """
        Iterate through blocks and remove duplicates.

        Args:
            blocks (List[SayouBlock]): The input list of blocks.

        Returns:
            List[SayouBlock]: A new list with duplicates removed.
        """
        seen_hashes: Set[int] = set()
        unique_blocks: List[SayouBlock] = []

        for block in blocks:
            # Generate stable hash key
            if isinstance(block.content, dict):
                content_str = json.dumps(block.content, sort_keys=True)
            else:
                content_str = str(block.content)

            if len(content_str) < 5:
                unique_blocks.append(block)
                continue

            content_hash = hash(content_str)

            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_blocks.append(block)

        return unique_blocks
