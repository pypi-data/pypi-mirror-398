"""Document readers for PDF, Excel, and Word files."""

from .pdf_reader import get_pdf_content
from .excel_reader import get_excel_content
from .word_reader import get_word_content

__all__ = ["get_pdf_content", "get_excel_content", "get_word_content"]
