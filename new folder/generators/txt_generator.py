"""LegalEase - Plain Text Document Generator.

Generates clean, professional UTF-8 plain text files from legal document content.
"""

from io import BytesIO
from typing import Optional


def generate_txt_bytes(
    content: str,
    title: Optional[str] = None,
    company_name: Optional[str] = None,
    footer_text: Optional[str] = None,
) -> bytes:
    """Generates clean UTF-8 text file bytes from legal document content."""
    lines = []
    if company_name and company_name.strip():
        lines.append(f"ORGANIZATION: {company_name.strip()}")
    if title and title.strip():
        lines.append(f"DOCUMENT: {title.strip()}")
    if company_name or title:
        lines.append("=" * 70)
        lines.append("")

    lines.append(content.strip())

    if footer_text and footer_text.strip():
        lines.append("")
        lines.append("-" * 70)
        lines.append(f"CONFIDENTIAL - {footer_text.strip()}")

    full_text = "\n".join(lines) + "\n"
    return full_text.encode("utf-8")
