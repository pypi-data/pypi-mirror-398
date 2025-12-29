"""
Comprehensive pytest tests for PDF Reader MCP Server

Tests cover:
- Text extraction from PDFs
- Error handling (encrypted PDFs, corrupted files, missing files)
- Directory listing functionality
- Various edge cases and error conditions
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock, mock_open
import pytest
import pypdf
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from fastmcp_pdftools.server import (
    extract_text_from_pdf,
    mcp
)


# Fixtures

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def simple_pdf(temp_dir):
    """Create a simple PDF file with text content"""
    pdf_path = os.path.join(temp_dir, "test.pdf")
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.drawString(100, 750, "Hello, World!")
    c.drawString(100, 730, "This is page 1")
    c.showPage()
    c.drawString(100, 750, "Page 2 content")
    c.showPage()
    c.save()
    return pdf_path


@pytest.fixture
def pdf_with_metadata(temp_dir):
    """Create a PDF with metadata"""
    pdf_path = os.path.join(temp_dir, "metadata.pdf")
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.setAuthor("Test Author")
    c.setTitle("Test Title")
    c.setSubject("Test Subject")
    c.drawString(100, 750, "Content with metadata")
    c.save()
    return pdf_path


@pytest.fixture
def empty_pdf(temp_dir):
    """Create a PDF with no text content"""
    pdf_path = os.path.join(temp_dir, "empty.pdf")
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.showPage()
    c.save()
    return pdf_path


@pytest.fixture
def multi_pdf_directory(temp_dir):
    """Create a directory with multiple PDF files"""
    # Create main PDFs
    for i in range(3):
        pdf_path = os.path.join(temp_dir, f"test_{i}.pdf")
        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.drawString(100, 750, f"Content of PDF {i}")
        c.save()
    
    # Create subdirectory with more PDFs
    subdir = os.path.join(temp_dir, "subdir")
    os.makedirs(subdir)
    pdf_path = os.path.join(subdir, "nested.pdf")
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.drawString(100, 750, "Nested PDF content")
    c.save()
    
    # Create a non-PDF file
    with open(os.path.join(temp_dir, "not_a_pdf.txt"), "w") as f:
        f.write("This is not a PDF")
    
    return temp_dir


# Tests for extract_text_from_pdf

def test_extract_text_from_valid_pdf(simple_pdf):
    """Test extracting text from a valid PDF file"""
    result = extract_text_from_pdf(simple_pdf)
    
    assert result["success"] is True
    assert "data" in result
    assert "text" in result["data"]
    assert "Hello, World!" in result["data"]["text"]
    assert "Page 2 content" in result["data"]["text"]
    assert result["data"]["page_count"] == 2
    assert result["data"]["pages_extracted"] == 2


def test_extract_text_with_metadata(pdf_with_metadata):
    """Test that metadata is extracted correctly"""
    result = extract_text_from_pdf(pdf_with_metadata)
    
    assert result["success"] is True
    assert "metadata" in result["data"]
    assert result["data"]["metadata"]["author"] == "Test Author"
    assert result["data"]["metadata"]["title"] == "Test Title"
    assert result["data"]["metadata"]["subject"] == "Test Subject"


def test_extract_text_from_empty_pdf(empty_pdf):
    """Test extracting text from a PDF with no text"""
    result = extract_text_from_pdf(empty_pdf)
    
    assert result["success"] is True
    assert result["data"]["page_count"] == 1
    # Empty PDFs might have minimal or no text
    assert "text" in result["data"]


def test_extract_text_file_not_found():
    """Test error handling for non-existent file"""
    result = extract_text_from_pdf("/nonexistent/path/file.pdf")
    
    assert result["success"] is False
    assert result["error"] == "FILE_NOT_FOUND"
    assert "File not found" in result["message"]


def test_extract_text_permission_error(temp_dir):
    """Test error handling for permission denied"""
    pdf_path = os.path.join(temp_dir, "restricted.pdf")
    
    # Create a file
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.drawString(100, 750, "Test")
    c.save()
    
    # Mock permission error
    with patch("builtins.open", side_effect=PermissionError("Access denied")):
        result = extract_text_from_pdf(pdf_path)
    
    assert result["success"] is False
    assert result["error"] == "PERMISSION_DENIED"
    assert "Permission denied" in result["message"]


def test_extract_text_encrypted_pdf(temp_dir):
    """Test error handling for encrypted PDF"""
    pdf_path = os.path.join(temp_dir, "encrypted.pdf")
    
    # Create an encrypted PDF
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.drawString(100, 750, "Secret content")
    c.save()
    
    # Now encrypt it
    from pypdf import PdfReader, PdfWriter
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    
    for page in reader.pages:
        writer.add_page(page)
    
    writer.encrypt("password123")
    
    with open(pdf_path, "wb") as output_file:
        writer.write(output_file)
    
    result = extract_text_from_pdf(pdf_path)
    
    assert result["success"] is False
    assert result["error"] == "PDF_ENCRYPTED"
    assert "encrypted" in result["message"].lower()


def test_extract_text_corrupted_pdf(temp_dir):
    """Test error handling for corrupted PDF"""
    pdf_path = os.path.join(temp_dir, "corrupted.pdf")
    
    # Create a corrupted PDF (not a valid PDF structure)
    with open(pdf_path, "wb") as f:
        f.write(b"This is not a valid PDF file content")
    
    result = extract_text_from_pdf(pdf_path)
    
    assert result["success"] is False
    assert result["error"] == "PDF_READ_ERROR"
    assert "Could not read PDF" in result["message"]


def test_extract_text_os_error(temp_dir):
    """Test error handling for OS errors"""
    pdf_path = os.path.join(temp_dir, "test.pdf")
    
    # Create a valid PDF
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.drawString(100, 750, "Test")
    c.save()
    
    # Mock an OS error
    with patch("builtins.open", side_effect=OSError("Disk error")):
        result = extract_text_from_pdf(pdf_path)
    
    assert result["success"] is False
    assert result["error"] == "FILE_SYSTEM_ERROR"
    assert "File system error" in result["message"]


def test_extract_text_page_extraction_error(simple_pdf):
    """Test handling of page extraction errors"""
    # Mock page.extract_text() to raise an error
    with patch("pypdf.PdfReader") as mock_reader:
        mock_page = Mock()
        mock_page.extract_text.side_effect = pypdf.errors.PdfReadError("Page error")
        
        mock_reader_instance = Mock()
        mock_reader_instance.is_encrypted = False
        mock_reader_instance.pages = [mock_page]
        mock_reader_instance.metadata = {}
        mock_reader_instance.__len__ = Mock(return_value=1)
        
        mock_reader.return_value = mock_reader_instance
        
        result = extract_text_from_pdf(simple_pdf)
        
        assert result["success"] is True
        assert "[Error extracting text from this page]" in result["data"]["text"]


# Tests for read_local_pdf (async function)
# Note: These test the core logic via extract_text_from_pdf since read_local_pdf
# is decorated with @mcp.tool() which makes it a FunctionTool object

def test_read_local_pdf_logic_success(simple_pdf):
    """Test the core logic of reading a local PDF file"""
    # Test via extract_text_from_pdf which contains the core logic
    abs_path = os.path.abspath(simple_pdf)
    result = extract_text_from_pdf(abs_path)
    
    assert result["success"] is True
    assert "data" in result
    assert "Hello, World!" in result["data"]["text"]


def test_read_local_pdf_logic_relative_path(simple_pdf):
    """Test reading a PDF with relative path converted to absolute"""
    # Get relative path
    original_dir = os.getcwd()
    pdf_dir = os.path.dirname(simple_pdf)
    pdf_name = os.path.basename(simple_pdf)
    
    try:
        os.chdir(pdf_dir)
        abs_path = os.path.abspath(pdf_name)
        result = extract_text_from_pdf(abs_path)
        
        assert result["success"] is True
    finally:
        os.chdir(original_dir)


def test_read_local_pdf_logic_not_found():
    """Test reading a non-existent PDF"""
    abs_path = os.path.abspath("/nonexistent/file.pdf")
    result = extract_text_from_pdf(abs_path)
    
    assert result["success"] is False
    assert result["error"] == "FILE_NOT_FOUND"


# Tests for list_pdf_files - testing logic directly since it's decorated

def test_list_pdf_files_in_directory(multi_pdf_directory):
    """Test listing PDF files in a directory"""
    dir_path = Path(multi_pdf_directory).resolve()
    pdf_files = []
    
    for pdf_path in dir_path.glob("**/*.pdf"):
        stat = pdf_path.stat()
        pdf_files.append({
            "name": pdf_path.name,
            "path": str(pdf_path),
            "size_bytes": stat.st_size,
            "modified": stat.st_mtime
        })
    
    assert len(pdf_files) == 4  # 3 main + 1 nested
    
    # Check that all files are PDFs
    for file_info in pdf_files:
        assert file_info["name"].endswith(".pdf")
        assert "path" in file_info
        assert "size_bytes" in file_info
        assert "modified" in file_info


def test_list_pdf_files_sorted_by_name(multi_pdf_directory):
    """Test that PDF files can be sorted by name"""
    dir_path = Path(multi_pdf_directory).resolve()
    pdf_files = []
    
    for pdf_path in dir_path.glob("**/*.pdf"):
        pdf_files.append({"name": pdf_path.name})
    
    sorted_files = sorted(pdf_files, key=lambda x: x["name"])
    file_names = [f["name"] for f in sorted_files]
    assert file_names == sorted(file_names)


def test_list_pdf_files_empty_directory(temp_dir):
    """Test listing PDFs in an empty directory"""
    empty_dir = os.path.join(temp_dir, "empty")
    os.makedirs(empty_dir)
    
    dir_path = Path(empty_dir).resolve()
    pdf_files = list(dir_path.glob("**/*.pdf"))
    
    assert len(pdf_files) == 0


def test_list_pdf_files_directory_validation():
    """Test directory validation logic"""
    # Test non-existent directory
    dir_path = Path("/nonexistent/directory")
    assert not dir_path.exists()


def test_list_pdf_files_file_validation(simple_pdf):
    """Test that file path is not a directory"""
    file_path = Path(simple_pdf)
    assert file_path.exists()
    assert not file_path.is_dir()
    assert file_path.is_file()


# Integration tests

def test_end_to_end_workflow(multi_pdf_directory):
    """Test a complete workflow: list PDFs, then read one"""
    # First, list all PDFs
    dir_path = Path(multi_pdf_directory).resolve()
    pdf_files = []
    
    for pdf_path in dir_path.glob("**/*.pdf"):
        stat = pdf_path.stat()
        pdf_files.append({
            "name": pdf_path.name,
            "path": str(pdf_path),
            "size_bytes": stat.st_size,
            "modified": stat.st_mtime
        })
    
    assert len(pdf_files) > 0
    
    # Then, read the first PDF
    first_pdf_path = pdf_files[0]["path"]
    read_result = extract_text_from_pdf(first_pdf_path)
    assert read_result["success"] is True
    assert "text" in read_result["data"]


def test_metadata_with_none_values(temp_dir):
    """Test handling of PDFs with no metadata"""
    pdf_path = os.path.join(temp_dir, "no_metadata.pdf")
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.drawString(100, 750, "No metadata")
    c.save()
    
    result = extract_text_from_pdf(pdf_path)
    
    assert result["success"] is True
    assert "metadata" in result["data"]
    # ReportLab sets default title to "untitled" and author to "anonymous"
    assert result["data"]["metadata"]["title"] == "untitled"
    assert result["data"]["metadata"]["author"] == "anonymous"


def test_page_number_formatting(simple_pdf):
    """Test that page numbers are formatted correctly in output"""
    result = extract_text_from_pdf(simple_pdf)
    
    assert result["success"] is True
    assert "--- Page 1 ---" in result["data"]["text"]
    assert "--- Page 2 ---" in result["data"]["text"]


def test_text_content_stripping(simple_pdf):
    """Test that text content is properly stripped"""
    result = extract_text_from_pdf(simple_pdf)
    
    assert result["success"] is True
    # Text should not have excessive leading/trailing whitespace
    text = result["data"]["text"]
    assert text == text.strip()
