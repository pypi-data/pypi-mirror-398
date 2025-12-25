import re
from typing import List

from sayou.core.registry import register_component
from sayou.core.schemas import SayouBlock

from ..interfaces.base_processor import BaseProcessor


@register_component("processor")
class PiiMasker(BaseProcessor):
    """
    (Tier 2) Masks Personally Identifiable Information (PII) in text blocks.

    Uses Regex patterns to identify and redact sensitive data like emails
    and phone numbers in 'text' and 'md' blocks.
    """

    component_name = "PiiMasker"

    @classmethod
    def can_handle(cls, blocks: list) -> float:
        return 1.0 if super().can_handle(blocks) > 0 else 0.0

    def initialize(self, mask_email: bool = True, mask_phone: bool = True, **kwargs):
        """
        Configure masking targets.

        Args:
            mask_email (bool): Whether to mask email addresses (default: True).
            mask_phone (bool): Whether to mask phone numbers (default: True).
            **kwargs: Additional arguments.
        """
        self.mask_email = mask_email
        self.mask_phone = mask_phone
        self._email_re = re.compile(r"[\w\.-]+@[\w\.-]+")
        # Simple phone regex (customizable)
        self._phone_re = re.compile(r"\d{3}[-\.\s]??\d{3,4}[-\.\s]??\d{4}")

    def _do_process(self, blocks: List[SayouBlock]) -> List[SayouBlock]:
        """
        Apply masking regex to text content.

        Args:
            blocks (List[SayouBlock]): Input blocks.

        Returns:
            List[SayouBlock]: Blocks with sensitive info replaced by tokens.
        """
        for block in blocks:
            if block.type not in ["text", "md"] or not isinstance(block.content, str):
                continue

            if self.mask_email:
                block.content = self._email_re.sub("[EMAIL]", block.content)
            if self.mask_phone:
                block.content = self._phone_re.sub("[PHONE]", block.content)

        return blocks
