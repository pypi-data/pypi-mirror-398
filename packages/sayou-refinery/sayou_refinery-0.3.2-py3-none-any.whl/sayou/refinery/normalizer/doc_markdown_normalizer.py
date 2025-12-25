from typing import Any, Dict, List

from sayou.core.registry import register_component
from sayou.core.schemas import SayouBlock

from ..core.exceptions import NormalizationError
from ..interfaces.base_normalizer import BaseNormalizer


@register_component("normalizer")
class DocMarkdownNormalizer(BaseNormalizer):
    """
    (Tier 2) Normalizes a Sayou Document Dictionary into Markdown SayouBlocks.

    This engine parses the structured dictionary output from 'sayou-document' and
    converts individual elements (Text, Table, Image, Chart) into semantically
    rich Markdown blocks. It also handles metadata conversion to Frontmatter.
    """

    component_name = "DocMarkdownNormalizer"
    SUPPORTED_TYPES = ["standard_doc", "sayou_doc_json"]

    @classmethod
    def can_handle(cls, raw_data: Any, strategy: str = "auto") -> float:
        if strategy in ["markdown", "standard_doc"]:
            return 1.0

        if hasattr(raw_data, "doc_type") and hasattr(raw_data, "pages"):
            return 1.0

        if isinstance(raw_data, str):
            if any(
                line.strip().startswith(("#", "-", "* "))
                for line in raw_data.splitlines()[:10]
            ):
                return 0.8
            return 0.1

        return 0.0

    def initialize(
        self,
        include_headers: bool = True,
        include_footers: bool = False,
        **kwargs,
    ):
        """
        Configure the normalizer's behavior regarding document structure.

        Args:
            include_headers (bool): If True, processes elements found in page headers.
            include_footers (bool): If True, processes elements found in page footers.
            **kwargs: Additional configuration parameters passed to parent.
        """
        super().initialize(**kwargs)
        self.include_headers = include_headers
        self.include_footers = include_footers

    def _do_normalize(self, raw_data: Any) -> List[SayouBlock]:
        """
        Execute the normalization logic on the document dictionary.

        Args:
            raw_data (Any): The input dictionary adhering to Sayou Document Schema.

        Returns:
            List[SayouBlock]: A list of normalized content blocks (mostly 'md' type).

        Raises:
            NormalizationError: If `raw_data` is not a valid dictionary.
        """
        # 1. Input Handling (Dict/Object/Str Safe Conversion)
        if isinstance(raw_data, str):
            return [SayouBlock(type="md", content=raw_data, metadata={})]

        # Handle Pydantic models or objects safely
        if hasattr(raw_data, "model_dump"):
            doc_data = raw_data.model_dump()
        elif hasattr(raw_data, "dict"):
            doc_data = raw_data.dict()
        elif hasattr(raw_data, "__dict__"):
            doc_data = raw_data.__dict__
        elif isinstance(raw_data, dict):
            doc_data = raw_data
        else:
            raise NormalizationError(
                f"Input must be convertible to Dictionary, got {type(raw_data).__name__}"
            )

        normalized_blocks: List[SayouBlock] = []

        doc_meta = doc_data.get("metadata", {})

        def sanitize_text(text: str) -> str:
            if not text:
                return ""
            text = text.replace("\x0b", "\n")
            text = text.replace("\r", "\n")
            text = text.replace("\f", "\n")
            return text

        # 2. Iterate Pages
        for page in doc_data.get("pages", []):
            page_content_buffer = []
            page_num = page.get("page_index", 0)

            # Helper to extract text from elements using existing logic
            def collect_text(elements, is_header=False, is_footer=False):
                if not elements:
                    return
                for element in elements:
                    sub_blocks = self._handle_element(element, is_header, is_footer)
                    for sb in sub_blocks:
                        if sb.content and sb.content.strip():
                            clean_content = sanitize_text(sb.content.strip())
                            page_content_buffer.append(clean_content)

            # A. Header Elements
            if self.include_headers:
                collect_text(page.get("header_elements", []), is_header=True)

            # B. Body Elements (Main Content)
            collect_text(page.get("elements", []), is_header=False)

            # C. Footer Elements
            if self.include_footers:
                collect_text(page.get("footer_elements", []), is_footer=True)

            # 3. Aggregate: Create ONE Block per Page
            if page_content_buffer:
                full_page_text = "\n\n".join(page_content_buffer)

                block_meta = doc_meta.copy()
                block_meta.update(
                    {
                        "page_num": page_num,
                        "origin_type": "page_aggregated",
                        "source": doc_meta.get("filename", "unknown"),
                    }
                )

                normalized_blocks.append(
                    SayouBlock(
                        type="md",
                        content=full_page_text,
                        metadata=block_meta,
                    )
                )

        return normalized_blocks

    def _handle_element(
        self, element: Dict[str, Any], is_header: bool, is_footer: bool
    ) -> List[SayouBlock]:
        """
        Dispatch the element to specific handlers based on its 'type' field.

        Args:
            element (Dict[str, Any]): The element dictionary.
            is_header (bool): True if the element is part of the page header.
            is_footer (bool): True if the element is part of the page footer.

        Returns:
            List[SayouBlock]: The resulting block(s) from the element.
        """
        if is_footer and not self.include_footers:
            return []

        elem_type = element.get("type")

        if elem_type == "text":
            return self._handle_text(element, is_header, is_footer)

        if elem_type == "table":
            return self._handle_table(element, is_header, is_footer)

        if elem_type == "image":
            return self._handle_image(element, is_header, is_footer)

        if elem_type == "chart":
            return self._handle_chart(element, is_header, is_footer)

        return []

    def _handle_doc_metadata(self, doc_data: Dict[str, Any]) -> List[SayouBlock]:
        """
        Convert document-level metadata into a Markdown Frontmatter block.

        Args:
            doc_data (Dict[str, Any]): The root document dictionary containing 'metadata'.

        Returns:
            List[SayouBlock]: A single block containing YAML-like frontmatter.
        """
        md_frontmatter = "---\n"
        metadata = doc_data.get("metadata", {})

        title = metadata.get("title")
        author = metadata.get("author")

        if title:
            md_frontmatter += f"title: {title}\n"
        if author:
            md_frontmatter += f"author: {author}\n"
        md_frontmatter += "---\n\n"

        return [
            SayouBlock(
                type="md",
                content=md_frontmatter,
                metadata={"page_num": 0, "id": "metadata", "is_footer": False},
            )
        ]

    def _handle_text(
        self, element: Dict[str, Any], is_header: bool, is_footer: bool
    ) -> List[SayouBlock]:
        """
        Convert a text element to a Markdown block, handling headings and lists.

        Uses 'semantic_type' (heading/list) and 'level' attributes to generate
        appropriate Markdown syntax (e.g., '# Title', '- Item').
        """
        text = element.get("text", "").strip()
        if not text:
            return []

        raw_attrs = element.get("raw_attributes", {})
        semantic_type = raw_attrs.get("semantic_type")

        content = None

        # 1. '●' (List) 처리
        if semantic_type == "list":
            level = raw_attrs.get("list_level", 0)
            indent = "  " * level
            content = f"{indent}- {text}"

        # 2. 'Heading 1-9' (제목) 처리
        elif semantic_type == "heading":
            level = raw_attrs.get("heading_level", 1)
            hashes = "#" * level
            content = f"{hashes} {text}"

        # 3. PPT 플레이스홀더 (레거시 호환)
        elif raw_attrs.get("placeholder_type") == "TITLE":
            content = f"# {text}"

        # 4. 그 외 (기본 텍스트)
        else:
            content = text

        return [
            SayouBlock(
                type="md",
                content=content,
                metadata={
                    "page_num": element.get("meta", {}).get("page_num"),
                    "id": element.get("id"),
                    "style": raw_attrs.get("style"),
                    "is_footer": is_footer,
                },
            )
        ]

    def _handle_table(
        self, element: Dict[str, Any], is_header: bool, is_footer: bool
    ) -> List[SayouBlock]:
        """
        Convert a table element into a Markdown table representation.

        Args:
            element (Dict[str, Any]): Must contain 'data' (2D list).
        """
        md_table = ""
        table_data = element.get("data", [])

        if not table_data:
            return []

        max_cols = 0
        for row in table_data:
            if row:
                max_cols = max(max_cols, len(row))

        if max_cols == 0:
            return []

        # 1. 헤더 행 (첫 번째 행)
        header = table_data[0]
        header_cells = list(map(str, header)) + [""] * (max_cols - len(header))
        md_table += "| " + " | ".join(header_cells) + " |\n"

        # 2. 구분자 행 (최대 열 개수 기준)
        md_table += "| " + " | ".join(["---"] * max_cols) + " |\n"

        # 3. 본문 행 (두 번째 행부터)
        for row in table_data[1:]:
            body_cells = list(map(str, row)) + [""] * (max_cols - len(row))
            md_table += "| " + " | ".join(body_cells) + " |\n"

        return [
            SayouBlock(
                type="md",
                content=md_table.strip(),
                metadata={
                    "page_num": element.get("meta", {}).get("page_num"),
                    "id": element.get("id"),
                    "is_footer": is_footer,
                },
            )
        ]

    def _handle_image(
        self, element: Dict[str, Any], is_header: bool, is_footer: bool
    ) -> List[SayouBlock]:
        """
        Process an image element.

        Depending on implementation, this might return an 'image_base64' block
        or a Markdown image link if an external URL is provided.
        """
        image_base64 = element.get("image_base64")
        image_base64 = element.get("image_base64")
        if not image_base64:
            return []

        ocr_text = (element.get("ocr_text") or "").strip()
        if not ocr_text:
            alt_text = "image"
        else:
            alt_text = ocr_text

        img_format = element.get("image_format", "png")

        return [
            SayouBlock(
                type="image_base64",
                content=image_base64,
                metadata={
                    "page_num": element.get("meta", {}).get("page_num"),
                    "id": element.get("id"),
                    "is_footer": is_footer,
                    "alt_text": alt_text,
                    "format": img_format,
                },
            )
        ]

    def _handle_chart(
        self, element: Dict[str, Any], is_header: bool, is_footer: bool
    ) -> List[SayouBlock]:
        """
        Convert a chart element into its text representation.

        Uses the 'text_representation' field from the element to create
        a descriptive text block for LLM consumption.
        """
        text_rep = element.get("text_representation")
        if not text_rep:
            return []

        content = f"--- Chart Data ---\n{text_rep}\n--------------------\n"

        return [
            SayouBlock(
                type="md",
                content=content,
                metadata={
                    "page_num": element.get("meta", {}).get("page_num"),
                    "id": element.get("id"),
                    "is_footer": is_footer,
                },
            )
        ]
