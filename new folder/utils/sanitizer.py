"""LegalEase - Text and Filename Sanitization Utilities.

Provides secure sanitization for filenames, HTML rendering, and text normalization.
"""

import html
import re
from typing import List


def sanitize_filename(name: str, ext: str = "txt") -> str:
    """Sanitize a document title or type into a safe, clean filename.

    Example: "Employment Contract (Full-time)" -> "LegalEase_Employment_Contract_Full_time.txt"
    """
    if not name or not name.strip():
        base = "LegalEase_Document"
    else:
        # Clean special characters
        cleaned = re.sub(r"[^\w\s\-]", "_", name.strip())
        # Replace spaces and multiple underscores with a single underscore
        cleaned = re.sub(r"[\s_]+", "_", cleaned)
        cleaned = cleaned.strip("._-")
        if not cleaned:
            cleaned = "Document"
        if not cleaned.lower().startswith("legalease"):
            base = f"LegalEase_{cleaned}"
        else:
            base = cleaned

    clean_ext = ext.lstrip(".").strip().lower() or "txt"
    return f"{base}.{clean_ext}"


def sanitize_html(text: str) -> str:
    """Escapes user and AI-generated strings before rendering into HTML.

    Prevents XSS attacks and injection of malicious scripts.
    """
    if not text:
        return ""
    return html.escape(text)


def clean_legal_text(text: str) -> str:
    """Normalizes whitespace, fixes line endings, and strips markdown code blocks if present."""
    if not text:
        return ""
    # Normalize Windows CRLF to LF
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")

    # Strip triple backtick markdown wrappers if the LLM outputted ```markdown ... ```
    triple_backtick_pattern = r"^```(?:markdown|text|txt)?\s*\n(.*?)\n```$"
    match = re.match(triple_backtick_pattern, normalized.strip(), re.DOTALL)
    if match:
        normalized = match.group(1)

    # Clean excessive empty lines (more than 2 consecutive newlines to 2)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def parse_terms_list(terms_raw: str) -> List[str]:
    """Parses user input terms separated by semicolons or newlines.

    Returns a clean list of individual terms.
    """
    if not terms_raw:
        return []

    # If semicolons exist, split on semicolons
    if ";" in terms_raw:
        parts = terms_raw.split(";")
    else:
        # Otherwise split on newlines
        parts = terms_raw.splitlines()

    terms = []
    for part in parts:
        cleaned = part.strip()
        # Remove leading bullet points, numbers, or dashes if present
        cleaned = re.sub(r"^(\d+[\.\)]\s*|[-*•]\s*)", "", cleaned).strip()
        if cleaned:
            terms.append(cleaned)

    return terms
