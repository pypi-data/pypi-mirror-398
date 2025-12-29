# esf-convert

Convert ECHO Single Form (ESF) XML files to Markdown or Word documents.

## Web Interface

Use the converter directly in your browser - no installation required:

**[Launch Web App](https://brianmcdonald.github.io/esf-convert/)**

The web app runs entirely client-side using WebAssembly. Your files are never uploaded to any server.

## Installation

```bash
uv tool install esf-convert
```

## Usage

```bash
# Convert to Word document (default)
esf-convert form.xml

# Convert to Markdown
esf-convert form.xml -f md

# Specify output file (format auto-detected from extension)
esf-convert form.xml -o report.md

# Explicit format with custom output name
esf-convert form.xml -f md -o my-report
```

### Options

| Option | Description |
|--------|-------------|
| `-o, --output` | Output file path (default: input filename with .docx extension) |
| `-f, --format` | Output format: `docx` (Word, default) or `md` (Markdown). Auto-detected from output extension if not specified. |

## Features

- **Structured output** - Chapters, sections, and subsections with proper heading hierarchy
- **Field tips** - Form guidelines/tips displayed in italics below each field heading
- **Enum labels** - Numeric values (0, 1, 2) converted to human-readable labels (No, Yes, Partially, etc.)
- **Outcome indicators** - Section 7.2 indicators with definition, baseline, target, and progress values
- **Results** - Section 7.3 results with indicators and activities
- **Metadata** - Reference numbers, dates, document type (YAML frontmatter in Markdown, table in DOCX)

## Development

Requires Python 3.10+.


