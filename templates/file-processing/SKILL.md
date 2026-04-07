---
name: {{SKILL_NAME}}
description: >
  Processes and transforms files including conversion, parsing, extraction,
  and batch operations. Use when reading/writing files, converting file formats,
  extracting content from documents, or batch processing multiple files.
  Trigger on: file processing, file conversion, content extraction,
  batch file operations.
compatibility:
  - Python 3.8+
---

# {{SKILL_NAME}}

Process and transform files efficiently.

## Prerequisites

Install dependencies:
```bash
pip install [required-packages]
```

## Usage

### Basic File Operations

```python
from scripts.processor import FileProcessor

processor = FileProcessor()
result = processor.process("input.txt")
print(result)
```

### Command Line

| Task | Command |
|------|---------|
| Process single | `python scripts/process.py --input file.txt` |
| Batch process | `python scripts/batch.py --dir ./input --pattern "*.txt"` |
| Convert format | `python scripts/convert.py --input data.csv --output data.json` |

## Configuration

```yaml
processing:
  encoding: utf-8
  buffer_size: 8192
  error_handling: skip  # skip, fail, or report
  output_dir: ./output
```

## Supported Formats

| Format | Extensions | Notes |
|--------|------------|-------|
| Text | .txt, .md | Plain text processing |
| CSV | .csv | Pandas DataFrame support |
| JSON | .json | Nested structure handling |
| XML | .xml | ElementTree parsing |

## Error Handling

| Error | Handling |
|-------|----------|
| File not found | Report error, continue batch |
| Encoding error | Try alternative encodings |
| Size limit exceeded | Stream processing mode |

## References

- `references/format-specs.md` - Format specifications
- `references/examples.md` - Usage examples
