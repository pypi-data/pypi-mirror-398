# docx_json_converter

A robust Python package for converting .docx files into structured JSON and back again. Designed for AI agents that need to read or generate Microsoft Word documents with high fidelity.

## Features

- **Round-Trip Formatting**: Preserves Bold, Italic, Underline, and Font Size.
- **Run-Level Precision**: Handles mixed formatting within paragraphs (e.g., "Hello **World**").
- **Column Support**: Detects and applies document-wide column layouts (e.g., 2-column newsletters).
- **Structure**: Supports Paragraphs, Bullet Lists, and Headers.
- **AI-Ready**: Generates optimized JSON schemas for LLMs.

## Installation

```bash
pip install docx_json_converter
```

(Or install locally for development):
```bash
pip install -e .
```

## Quick Start

### 1. Python API

```python
from docx_json_converter import convert_docx_to_json, convert_json_to_docx

# Convert DOCX -> JSON
data = convert_docx_to_json("input.docx")
# data = {"metadata": {"columns": 1}, "blocks": [...]}

# Convert JSON -> DOCX
convert_json_to_docx(data, "output.docx")
```

**Simplified Mode (Text Only):**
```python
# Returns blocks without detailed formatting/runs
data = convert_docx_to_json("input.docx", include_formatting=False)
```

### 2. CLI for AI Prompts

To teach an LLM (like ChatGPT or Claude) how to generate documents using this package, generate the system prompt file:

```bash
docx-json-prompt
```

This creates `llm.txt` with the JSON schema and rules.

## The Zen of docx_json_converter

```python
import docx_json_converter
docx_json_converter.zen()
```

## JSON Schema Example

```json
{
  "metadata": {
    "columns": 2
  },
  "blocks": [
    {
      "text": "My Title",
      "block_type": "title",
      "formatting": { "alignment": "center" },
      "runs": [
        { "text": "My Title", "formatting": { "bold": true, "font_size": 16.0 } }
      ]
    },
    {
      "text": "Bullet point 1",
      "block_type": "list_item",
      "formatting": { "alignment": "left" }
    }
  ]
}
```

## License

MIT

