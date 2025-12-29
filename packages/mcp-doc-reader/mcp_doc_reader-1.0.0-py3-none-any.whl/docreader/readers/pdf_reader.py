"""PDF document reader using pdfminer.six."""

import os
from pdfminer.high_level import extract_text


def get_pdf_content(file_path: str) -> str:
    """
    Read text content from a PDF file.
    
    Args:
        file_path: Path to the PDF file.
        
    Returns:
        Extracted text content as a string.
    """
    if not os.path.isabs(file_path):
        file_path = os.path.abspath(file_path)

    if not os.path.exists(file_path):
        return f"Error: File not found at {file_path}"
    
    try:
        text = extract_text(file_path)
        return text
    except Exception as e:
        return f"Error reading PDF: {e}"
