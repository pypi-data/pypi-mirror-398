try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from typing import Any, List

from sayou.core.registry import register_component
from sayou.core.schemas import SayouBlock

from ..core.exceptions import NormalizationError
from ..interfaces.base_normalizer import BaseNormalizer


@register_component("normalizer")
class HtmlTextNormalizer(BaseNormalizer):
    """
    (Tier 2) Converts HTML string into a clean Text SayouBlock.

    Uses BeautifulSoup to strip tags, scripts, and styles, returning only
    the visible text content while preserving paragraph structure.
    """

    component_name = "HtmlTextNormalizer"
    SUPPORTED_TYPES = ["html"]

    @classmethod
    def can_handle(cls, raw_data: Any, strategy: str = "auto") -> float:
        if strategy in ["html"]:
            return 1.0

        if isinstance(raw_data, str):
            sample = raw_data[:1000].lower()
            if "<html" in sample or "<body" in sample or "<div" in sample:
                return 0.9

        return 0.0

    def _do_normalize(self, raw_data: Any) -> List[SayouBlock]:
        """
        Parse HTML and extract text.

        Args:
            raw_data (Any): The input HTML string.

        Returns:
            List[SayouBlock]: A single block of type 'text'.

        Raises:
            ImportError: If BeautifulSoup4 is not installed.
            NormalizationError: If input is not a string.
        """
        if not BeautifulSoup:
            raise ImportError("BeautifulSoup4 is required for HtmlTextNormalizer.")

        if not isinstance(raw_data, str):
            raise NormalizationError(
                f"Input must be HTML string, got {type(raw_data)}."
            )

        soup = BeautifulSoup(raw_data, "html.parser")

        for tag in soup(["script", "style", "noscript", "iframe"]):
            tag.extract()

        text = soup.get_text(separator="\n")

        import re

        text = re.sub(r"\n{3,}", "\n\n", text).strip()

        return [SayouBlock(type="text", content=text, metadata={"strategy": "html"})]
