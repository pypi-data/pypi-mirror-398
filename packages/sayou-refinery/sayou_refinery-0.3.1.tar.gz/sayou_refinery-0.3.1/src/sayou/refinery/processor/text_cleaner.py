import re
from typing import List

from sayou.core.registry import register_component
from sayou.core.schemas import SayouBlock

from ..interfaces.base_processor import BaseProcessor


@register_component("processor")
class TextCleaner(BaseProcessor):
    """
    (Tier 2) Cleans text content using regex and whitespace normalization.

    Operates on 'text' and 'md' blocks to remove noise characters or custom patterns.
    """

    component_name = "TextCleaner"

    @classmethod
    def can_handle(cls, blocks: list) -> float:
        if super().can_handle(blocks) > 0:
            return 1.0
        return 0.0

    def initialize(
        self, patterns: List[str] = None, normalize_space: bool = True, **kwargs
    ):
        """
        Configure cleaning patterns.

        Args:
            patterns (List[str]): List of regex patterns to remove from text.
            normalize_space (bool): If True, collapses multiple spaces/tabs/newlines.
            **kwargs: Additional arguments.
        """
        self.normalize_space = normalize_space
        self.patterns = [re.compile(p) for p in (patterns or [])]
        self._space_re = re.compile(r"[ \t]+")

    def _do_process(self, blocks: List[SayouBlock]) -> List[SayouBlock]:
        """
        Apply cleaning logic to text blocks.

        Args:
            blocks (List[SayouBlock]): Input blocks.

        Returns:
            List[SayouBlock]: Cleaned blocks.
        """
        for block in blocks:
            if block.type not in ["text", "md"]:
                continue

            if not isinstance(block.content, str):
                continue

            text = block.content

            # 1. Custom Patterns Removal
            for pat in self.patterns:
                text = pat.sub("", text)

            # 2. Whitespace Normalization
            if self.normalize_space:
                text = self._space_re.sub(" ", text)

            block.content = text.strip()

        return blocks
