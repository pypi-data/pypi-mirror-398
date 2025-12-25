# Donkit Read Engine

Document extraction toolkit for Donkit RagOps. It reads multiple document formats and exports content as text, JSON, or Markdown while preserving page-level structure where possible.

## Features

- Supported formats: PDF, DOCX/DOC, PPTX, XLSX/XLS, TXT, CSV, JSON, Images (PNG/JPG/JPEG)
- Outputs: text, json, markdown
- PDF engines:
  - Structured PyMuPDF-based processor (no external AI required)
  - unstructured.partition.pdf with OCR (Tesseract) and strategies (fast, hi_res, ocr_only, auto)
- OCR with configurable languages (e.g., rus+eng)
- Recursive directory processing
- Image reader with VLM for high-level image understanding

## Project Layout

- CLI entry: `donkit.read_engine.read_engine:main`
- Core reader: [donkit.read_engine.read_engine.DonkitReader](cci:2://file:///Users/romanlosev/donkit/platform/ragops-agent/shared/read-engine/src/donkit/read_engine/read_engine.py:40:0-204:37)
- PDF parsing: `donkit.read_engine.readers.portable_document_format.pdf_parser`
- Image handler: [donkit.read_engine.readers.static_visual_format.handler.image_read_handler](cci:1://file:///Users/romanlosev/donkit/platform/ragops-agent/shared/read-engine/src/donkit/read_engine/readers/static_visual_format/handler.py:7:0-17:40)
- Other handlers: text, JSON, Excel, Word, PowerPoint

Key files:
- [src/donkit/read_engine/read_engine.py](cci:7://file:///Users/romanlosev/donkit/platform/ragops-agent/shared/read-engine/src/donkit/read_engine/read_engine.py:0:0-0:0)
- [src/donkit/read_engine/readers/portable_document_format/pdf_parser.py](cci:7://file:///Users/romanlosev/donkit/platform/ragops-agent/shared/read-engine/src/donkit/read_engine/readers/portable_document_format/pdf_parser.py:0:0-0:0)
- [src/donkit/read_engine/readers/static_visual_format/handler.py](cci:7://file:///Users/romanlosev/donkit/platform/ragops-agent/shared/read-engine/src/donkit/read_engine/readers/static_visual_format/handler.py:0:0-0:0)

## Requirements

- Python: >= 3.12, < 4.0
- Poetry for dependency management
- Core packages (see [pyproject.toml](cci:7://file:///Users/romanlosev/donkit/platform/ragops-agent/shared/read-engine/pyproject.toml:0:0-0:0)): pymupdf, unstructured[pdf], pypdf, python-docx, python-pptx, pandas, pillow, loguru, etc.
- For OCR (optional):
  - Tesseract with language packs (e.g., rus, eng)
  - macOS (Homebrew):
    ```bash
    brew install tesseract
    brew install tesseract-lang
    ```
  - Verify languages: `tesseract --list-langs` (look for `rus`, `eng`)

## Installation

```bash
cd ragops-agent/shared/read-engine
poetry install
poetry shell
```

## Using DonkitReader Class

### Initialization

```python
from donkit.read_engine.read_engine import DonkitReader

# Create reader instance
reader = DonkitReader()
```

The constructor automatically:
- Detects available LLM credentials (OpenAI, Vertex AI) to choose PDF processing strategy
- Registers handlers for all supported file extensions
- Configures lazy imports for optional dependencies

### Main Method: `read_document()`

```python
def read_document(
    self,
    file_path: str,
    output_type: Literal["text", "json", "markdown"]
) -> str
```

**Parameters:**
- `file_path` (str): Path to the input file (local filesystem)
- `output_type` (Literal): Output format - `"text"`, `"json"`, or `"markdown"`

**Returns:**
- `str`: Path to the processed output file in `processed/` subdirectory

**Raises:**
- `RuntimeError`: If document processing fails
- `ValueError`: If file extension is not supported

### Usage Examples

#### Basic Document Reading

```python
from donkit.read_engine.read_engine import DonkitReader

reader = DonkitReader()

# Process PDF to JSON
output_path = reader.read_document("./docs/report.pdf", output_type="json")
print(f"Processed file saved to: {output_path}")
# Output: ./docs/processed/report.json

# Process Word document to Markdown
output_path = reader.read_document("./docs/memo.docx", output_type="markdown")
# Output: ./docs/processed/memo.md

# Process image to JSON
output_path = reader.read_document("./images/chart.png", output_type="json")
# Output: ./images/processed/chart.json
```

#### Reading and Parsing Output

```python
import json
from pathlib import Path

reader = DonkitReader()

# Process document
output_path = reader.read_document("./report.pdf", output_type="json")

# Read the output
with open(output_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Access content
for item in data["content"]:
    page = item.get("page", 0)
    item_type = item.get("type", "")
    content = item.get("content", "")
    
    print(f"Page {page} ({item_type}): {content[:100]}...")
```

#### Batch Processing

```python
from pathlib import Path

reader = DonkitReader()
input_dir = Path("./documents")

# Process all supported files in directory
for file_path in input_dir.rglob("*"):
    if file_path.suffix.lower() in reader.readers:
        try:
            output = reader.read_document(
                str(file_path), 
                output_type="json"
            )
            print(f"✓ Processed: {file_path.name}")
        except Exception as e:
            print(f"✗ Failed {file_path.name}: {e}")
```

#### Format-Specific Processing

```python
reader = DonkitReader()

# PDF with OCR (set env vars before creating reader)
import os
# Language format: "rus+eng" will be converted to ["rus", "eng"] internally
os.environ["UNSTRUCTURED_OCR_LANG"] = "rus+eng"
os.environ["UNSTRUCTURED_STRATEGY"] = "hi_res"

output = reader.read_document("./scan.pdf", output_type="json")

# Excel to text
output = reader.read_document("./data.xlsx", output_type="text")

# PowerPoint to markdown
output = reader.read_document("./presentation.pptx", output_type="markdown")
```

### Supported File Extensions

The `readers` dictionary maps extensions to handlers:

```python
reader.readers.keys()
# dict_keys(['.txt', '.json', '.csv', '.pdf', '.docx', '.doc', 
#            '.pptx', '.xlsx', '.xls', '.png', '.jpg', '.jpeg'])
```

### Output Structure

#### JSON Format

```json
{
  "content": [
    {
      "page": 1,
      "type": "Text",
      "content": "Document text content..."
    },
    {
      "page": 1,
      "type": "Image",
      "content": "Image analysis result...",
      "image_index": 0
    },
    {
      "page": 2,
      "type": "Text",
      "content": "More content..."
    }
  ]
}
```

#### Markdown Format

```markdown
## Page 1

Document text content...

### Image on Page 1

Image analysis result...

## Page 2

More content...
```

#### Text Format

```
Document text content...
Image analysis result...
More content...
```

### Advanced: Custom Processing Pipeline

```python
from donkit.read_engine.read_engine import DonkitReader
from pathlib import Path
import json

class CustomDocumentProcessor:
    def __init__(self):
        self.reader = DonkitReader()
    
    def process_with_metadata(self, file_path: str):
        """Process document and add custom metadata."""
        # Process document
        output_path = self.reader.read_document(
            file_path, 
            output_type="json"
        )
        
        # Load and enhance
        with open(output_path, "r") as f:
            data = json.load(f)
        
        # Add metadata
        data["metadata"] = {
            "source_file": file_path,
            "page_count": len(set(
                item.get("page", 0) 
                for item in data["content"]
            )),
            "has_images": any(
                item.get("type") == "Image" 
                for item in data["content"]
            )
        }
        
        # Save enhanced version
        enhanced_path = output_path.replace(".json", "_enhanced.json")
        with open(enhanced_path, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return enhanced_path

# Usage
processor = CustomDocumentProcessor()
result = processor.process_with_metadata("./report.pdf")
```

### Error Handling

```python
from donkit.read_engine.read_engine import DonkitReader

reader = DonkitReader()

try:
    output = reader.read_document("./file.pdf", output_type="json")
except ValueError as e:
    # Unsupported file extension
    print(f"Unsupported format: {e}")
except RuntimeError as e:
    # Processing failed
    print(f"Processing error: {e}")
except Exception as e:
    # Other errors
    print(f"Unexpected error: {e}")
