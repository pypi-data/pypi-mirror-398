# sayou-refinery

[![PyPI version](https://img.shields.io/pypi/v/sayou-refinery.svg?color=blue)](https://pypi.org/project/sayou-refinery/)
[![License](https://img.shields.io/badge/License-Apache%202.0-red.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![Docs](https://img.shields.io/badge/docs-mkdocs-success.svg?logo=materialformkdocs)](https://sayouzone.github.io/sayou-fabric/library-guides/refinery/)

**The Universal Data Cleaning & Normalization Engine for Sayou Fabric.**

`sayou-refinery` acts as the "Cleaning Plant" in your data pipeline.

It transforms heterogeneous raw data (JSON Documents, HTML, DB Records) into a standardized stream of **SayouBlocks**, ensuring that downstream components (like Chunkers or LLMs) receive clean, uniform data regardless of the original source format.

## 💡 Core Philosophy

**"Flatten Structure, Polish Content."**

Refinery operates in two distinct stages to guarantee data quality:

1.  **Normalization (Shape Shifting):** Converts complex structures (nested JSON, HTML trees, DB Rows) into a linear list of `SayouBlocks`.
2.  **Processing (Cleaning):** Applies a chain of cleaning agents (Regex, Masking, Deduplication) to improve data hygiene.

## 📦 Installation

```bash
pip install sayou-refinery
```

## ⚡ Quick Start

The `RefineryPipeline` orchestrates the normalization and processing chain.

```python
from sayou.refinery.pipeline import RefineryPipeline

def run_demo():
    # 1. Initialize with specific cleaning rules
    pipeline = RefineryPipeline()
    pipeline.initialize(
        mask_email=True,
        outlier_rules={"price": {"min": 0, "max": 1000, "action": "clamp"}}
    )

    # 2. Raw Data (e.g., from sayou-document)
    raw_doc = {
        "metadata": {"title": "Test Doc"},
        "pages": [{
            "elements": [
                {"type": "text", "text": "Contact: admin@sayou.ai"},
                {"type": "text", "text": "   Dirty   Whitespace   "}
            ]
        }]
    }

    # 3. Run Pipeline
    # strategy: 'standard_doc', 'html', 'json', etc.
    blocks = pipeline.run(raw_doc, strategy="standard_doc")

    # 4. Result
    for block in blocks:
        print(f"[{block.type}] {block.content}")
        
        # Output:
        # [md_meta] --- title: Test Doc ...
        # [md] Contact: [EMAIL]
        # [md] Dirty Whitespace

if __name__ == "__main__":
    run_demo()
```

## 🔑 Key Components

### Normalizers
* **`DocMarkdownNormalizer`**: Converts Sayou Document Dicts into Markdown blocks.
* **`HtmlTextNormalizer`**: Strips HTML tags and scripts, extracting clean text.
* **`RecordNormalizer`**: Converts DB rows or JSON objects into 'record' blocks.

### Processors
* **`TextCleaner`**: Normalizes whitespace and removes noise via regex.
* **`PiiMasker`**: Masks sensitive info like emails and phone numbers.
* **`Deduplicator`**: Removes duplicate content blocks.
* **`Imputer`**: Fills missing values in record blocks.
* **`OutlierHandler`**: Filters or clamps numerical outliers in records.

## 🤝 Contributing

We welcome contributions for new Normalizers (e.g., `CsvNormalizer`, `LogNormalizer`) or Processors (e.g., `LangChainFilter`).

## 📜 License

Apache 2.0 License © 2025 Sayouzone