"""LegalEase - Generators and Utilities Unit Tests.

Tests document exporters (TXT, DOCX, PDF), validators, sanitizers, and terms parsing.
"""

from io import BytesIO
from PIL import Image
import pytest

from generators.docx_generator import generate_docx_bytes
from generators.pdf_generator import generate_pdf_bytes
from generators.txt_generator import generate_txt_bytes
from utils.sanitizer import clean_legal_text, parse_terms_list, sanitize_filename, sanitize_html
from utils.validators import validate_document_request, validate_logo_file

SAMPLE_CONTENT = """# NON-DISCLOSURE AGREEMENT

SECTION 1. CONFIDENTIAL INFORMATION
The Receiving Party shall maintain confidentiality.

SECTION 2. TERM
This Agreement shall remain in effect for two (2) years.

IN WITNESS WHEREOF:
Disclosing Party: ____________________
Receiving Party: ____________________
"""


def test_sanitize_filename():
    """Tests filename sanitization logic."""
    assert sanitize_filename("Employment Contract", "txt") == "LegalEase_Employment_Contract.txt"
    assert sanitize_filename("NDA / Secret (2026)", "docx") == "LegalEase_NDA_Secret_2026.docx"
    assert sanitize_filename("", "pdf") == "LegalEase_Document.pdf"
    assert sanitize_filename("LegalEase_Custom_Doc", "txt") == "LegalEase_Custom_Doc.txt"


def test_sanitize_html():
    """Tests XSS prevention and HTML character escaping."""
    raw = "<script>alert('xss')</script> & 'quotes'"
    clean = sanitize_html(raw)
    assert "<script>" not in clean
    assert "&lt;script&gt;" in clean
    assert "&amp;" in clean


def test_clean_legal_text():
    """Tests text normalization and markdown wrapper stripping."""
    wrapped_text = "```markdown\n# AGREEMENT\n\nBody text\n```"
    assert clean_legal_text(wrapped_text) == "# AGREEMENT\n\nBody text"

    crlf_text = "Line 1\r\n\r\n\r\n\r\nLine 2"
    cleaned = clean_legal_text(crlf_text)
    assert "\r" not in cleaned
    assert "\n\n\n" not in cleaned


def test_parse_terms_list():
    """Tests semicolon and newline terms parsing."""
    semicolon_terms = "Term 1; Term 2; Term 3;"
    parsed = parse_terms_list(semicolon_terms)
    assert parsed == ["Term 1", "Term 2", "Term 3"]

    bullet_terms = "1. First Term\n- Second Term\n• Third Term"
    parsed_bullets = parse_terms_list(bullet_terms)
    assert parsed_bullets == ["First Term", "Second Term", "Third Term"]


def test_validate_document_request():
    """Tests input validation rules."""
    # Valid
    valid, errors = validate_document_request(
        document_type="NDA",
        parties="Alice and Bob",
        terms="Payment in 30 days",
        effective_date="2026-05-01",
    )
    assert valid is True
    assert len(errors) == 0

    # Missing fields
    valid_empty, errors_empty = validate_document_request(
        document_type="",
        parties="",
        terms="",
        effective_date="",
    )
    assert valid_empty is False
    assert len(errors_empty) >= 4


def test_validate_logo_file():
    """Tests logo file format and size checks."""
    # Create a tiny valid in-memory PNG
    img = Image.new("RGB", (30, 30), color="blue")
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format="PNG")
    valid_bytes = img_byte_arr.getvalue()

    is_valid, err = validate_logo_file(valid_bytes, "logo.png")
    assert is_valid is True
    assert err is None

    # Invalid extension
    is_valid_ext, err_ext = validate_logo_file(valid_bytes, "logo.exe")
    assert is_valid_ext is False
    assert "Unsupported image format" in err_ext

    # Corrupt data
    is_valid_corrupt, err_corrupt = validate_logo_file(b"not an image", "test.png")
    assert is_valid_corrupt is False


def test_txt_generator():
    """Tests plain text generator bytes output."""
    raw_bytes = generate_txt_bytes(
        content=SAMPLE_CONTENT,
        title="Non-Disclosure Agreement",
        company_name="Acme Corp",
        footer_text="Confidential",
    )
    assert isinstance(raw_bytes, bytes)
    text = raw_bytes.decode("utf-8")
    assert "ORGANIZATION: Acme Corp" in text
    assert "DOCUMENT: Non-Disclosure Agreement" in text
    assert "CONFIDENTIAL" in text
    assert "SECTION 1. CONFIDENTIAL INFORMATION" in text


def test_docx_generator():
    """Tests Word (.docx) document generator."""
    # Create a small dummy logo
    img = Image.new("RGB", (40, 40), color="navy")
    img_bytes = BytesIO()
    img.save(img_bytes, format="PNG")

    docx_bytes = generate_docx_bytes(
        content=SAMPLE_CONTENT,
        title="Non-Disclosure Agreement",
        company_name="Acme Corp",
        effective_date="May 1, 2026",
        footer_text="Confidential - Acme Corp",
        logo_bytes=img_bytes.getvalue(),
        terms="Term 1; Term 2; Term 3",
        include_terms_table=True,
    )
    assert isinstance(docx_bytes, bytes)
    assert len(docx_bytes) > 2000
    # A valid docx file is a ZIP archive starting with PK (0x50, 0x4B)
    assert docx_bytes[:2] == b"PK"


def test_pdf_generator():
    """Tests PDF document generator."""
    img = Image.new("RGB", (40, 40), color="gold")
    img_bytes = BytesIO()
    img.save(img_bytes, format="PNG")

    pdf_bytes = generate_pdf_bytes(
        content=SAMPLE_CONTENT,
        title="Non-Disclosure Agreement",
        company_name="Acme Corp",
        effective_date="May 1, 2026",
        footer_text="Confidential - Acme Corp",
        logo_bytes=img_bytes.getvalue(),
        terms="Term 1; Term 2; Term 3",
        include_terms_table=True,
    )
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    # A valid PDF starts with %PDF-
    assert pdf_bytes.startswith(b"%PDF-")
