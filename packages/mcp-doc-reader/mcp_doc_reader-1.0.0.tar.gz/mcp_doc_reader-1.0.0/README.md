# MCP Doc Reader

[English](README.md) | [中文](README-CN.md)

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that enables AI assistants to read and extract content from PDF, Excel, and Word documents.

## Features

- **PDF Reading**: Extract text content from PDF files using `pdfminer.six`
- **Excel Reading**: Read `.xlsx` and `.xls` files with formatted table output
- **Word Reading**: Extract text and tables from `.docx` files
- **Cross-Platform**: Works on Windows, Linux, and macOS
- **Unicode Support**: Full support for non-ASCII characters (Chinese, Japanese, etc.)

## Installation

### Using uvx (Recommended)

```bash
uvx mcp-doc-reader
```

### Using pip

```bash
pip install mcp-doc-reader
```

### From Source

```bash
git clone https://github.com/yourusername/mcp-doc-reader.git
cd mcp-doc-reader
pip install -e .
```

## Configuration

Add the following to your MCP client configuration (e.g., Claude Desktop, Cursor):

### Option 1: Using uvx (Recommended)

```json
{
  "mcpServers": {
    "DocReader": {
      "command": "uvx",
      "args": ["mcp-doc-reader"]
    }
  }
}
```

### Option 2: Using pip-installed command

```json
{
  "mcpServers": {
    "DocReader": {
      "command": "mcp-doc-reader"
    }
  }
}
```

### Option 3: Windows with Unicode Support

For Windows systems with non-ASCII file paths (e.g., Chinese characters):

```json
{
  "mcpServers": {
    "DocReader": {
      "command": "cmd",
      "args": [
        "/c",
        "chcp 65001 >nul && uvx mcp-doc-reader"
      ]
    }
  }
}
```

### Option 4: Linux/macOS with Python module

```json
{
  "mcpServers": {
    "DocReader": {
      "command": "python",
      "args": ["-m", "docreader"]
    }
  }
}
```

## Available Tools

### `read_pdf`

Read text content from a PDF file.

**Parameters:**
- `file_path` (string, required): Absolute path to the PDF file

**Example:**
```json
{
  "name": "read_pdf",
  "arguments": {
    "file_path": "/path/to/document.pdf"
  }
}
```

### `read_excel`

Read content from an Excel file (.xlsx or .xls).

**Parameters:**
- `file_path` (string, required): Absolute path to the Excel file

**Example:**
```json
{
  "name": "read_excel",
  "arguments": {
    "file_path": "/path/to/spreadsheet.xlsx"
  }
}
```

### `read_word`

Read text content from a Word file (.docx).

**Parameters:**
- `file_path` (string, required): Absolute path to the Word file

**Example:**
```json
{
  "name": "read_word",
  "arguments": {
    "file_path": "/path/to/document.docx"
  }
}
```

## Usage Examples

Once configured, you can ask your AI assistant to:

- "Read the contents of /path/to/report.pdf"
- "Extract data from /path/to/data.xlsx"
- "What does the document /path/to/memo.docx contain?"

## Development

### Setup Development Environment

```bash
git clone https://github.com/yourusername/mcp-doc-reader.git
cd mcp-doc-reader
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Build Package

```bash
pip install build
python -m build
```

### Publish to PyPI

```bash
pip install twine
twine upload dist/*
```

## Project Structure

```
mcp-doc-reader/
├── src/
│   └── docreader/
│       ├── __init__.py
│       ├── __main__.py
│       ├── server.py
│       └── readers/
│           ├── __init__.py
│           ├── pdf_reader.py
│           ├── excel_reader.py
│           └── word_reader.py
├── examples/
│   ├── mcp_config_pip.json
│   ├── mcp_config_uvx.json
│   ├── mcp_config_windows.json
│   └── mcp_config_linux.json
├── pyproject.toml
├── README.md
└── LICENSE
```

## Troubleshooting

### Windows: Unicode/Chinese filename issues

If you encounter issues with non-ASCII characters in file paths on Windows, use the Windows-specific configuration that sets the code page to UTF-8:

```json
{
  "mcpServers": {
    "DocReader": {
      "command": "cmd",
      "args": ["/c", "chcp 65001 >nul && mcp-doc-reader"]
    }
  }
}
```

### .doc files not supported

The Word reader only supports `.docx` format. To read `.doc` files, please convert them to `.docx` first using Microsoft Word or LibreOffice.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
