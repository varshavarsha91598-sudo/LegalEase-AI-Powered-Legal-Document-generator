"""LegalEase - PDF Document Generator.

Generates sleek, professional legal PDF documents using fpdf2,
including headers, footers with page counts, logos, tables, and signature blocks.
"""

from io import BytesIO
import os
import re
import tempfile
from typing import List, Optional

from fpdf import FPDF
from utils.sanitizer import parse_terms_list


class LegalPDF(FPDF):
    """Custom FPDF subclass with professional legal header and footer."""

    def __init__(self, footer_text: Optional[str] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.footer_text = footer_text or "LegalEase - Confidential Legal Document"

    def footer(self):
        # Position at 15 mm from bottom
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(130, 140, 150)

        # Left: Footer text; Right: Page X of Y
        text_left = self.footer_text
        text_right = f"Page {self.page_no()} of {{nb}}"

        self.cell(0, 10, text_left, border=0, align="L")
        self.set_x(-40)
        self.cell(0, 10, text_right, border=0, align="R")


def _sanitize_for_pdf(text: str) -> str:
    """Replaces smart quotes and unicode typography symbols with standard ASCII equivalents.

    Ensures compatibility across standard PDF core fonts.
    """
    if not text:
        return ""
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2014": " - ",
        "\u2013": " - ",
        "\u2026": "...",
        "\u2022": "*",
        "\u00a0": " ",
        "•": "*",
    }
    for orig, rep in replacements.items():
        text = text.replace(orig, rep)

    # Encode to latin-1 safe representation if core fonts are used
    return text.encode("latin-1", "replace").decode("latin-1")


def generate_pdf_bytes(
    content: str,
    title: Optional[str] = None,
    company_name: Optional[str] = None,
    effective_date: Optional[str] = None,
    footer_text: Optional[str] = None,
    logo_bytes: Optional[bytes] = None,
    terms: Optional[str] = None,
    include_terms_table: bool = True,
) -> bytes:
    """Generates a professional legal PDF document and returns bytes."""
    pdf = LegalPDF(footer_text=footer_text, orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(left=20, top=20, right=20)
    pdf.alias_nb_pages()
    pdf.add_page()

    # 1. Company Logo (Top Center)
    if logo_bytes:
        tmp_logo = None
        try:
            # Write to a temporary file for fpdf to read
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f:
                f.write(logo_bytes)
                tmp_logo = f.name

            # Center logo
            logo_width = 38
            x_pos = (210 - logo_width) / 2
            pdf.image(tmp_logo, x=x_pos, y=pdf.get_y(), w=logo_width)
            pdf.ln(logo_width + 2)
        except Exception:
            pass
        finally:
            if tmp_logo and os.path.exists(tmp_logo):
                try:
                    os.unlink(tmp_logo)
                except Exception:
                    pass

    # 2. Company Name
    if company_name and company_name.strip():
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(70, 85, 105)
        pdf.cell(0, 6, _sanitize_for_pdf(company_name.strip().upper()), align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    # 3. Document Title
    doc_title = title.strip() if title and title.strip() else "LEGAL AGREEMENT"
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(15, 34, 64)  # Deep Navy
    pdf.cell(0, 10, _sanitize_for_pdf(doc_title.upper()), align="C", new_x="LMARGIN", new_y="NEXT")

    # 4. Effective Date Subtitle
    if effective_date and effective_date.strip():
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(100, 110, 120)
        pdf.cell(0, 6, _sanitize_for_pdf(f"Effective Date: {effective_date.strip()}"), align="C", new_x="LMARGIN", new_y="NEXT")

    # Decorative dividing line
    pdf.ln(3)
    pdf.set_draw_color(200, 210, 225)
    pdf.set_line_width(0.5)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(6)

    # 5. Terms Table (if requested)
    if include_terms_table and terms:
        parsed_terms = parse_terms_list(terms)
        if len(parsed_terms) > 1:
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(15, 34, 64)
            pdf.cell(0, 7, "KEY TERMS & PROVISIONS SUMMARY", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)

            # Table Header
            pdf.set_fill_color(226, 232, 240)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(15, 34, 64)
            pdf.cell(15, 7, "No.", border=1, align="C", fill=True)
            pdf.cell(155, 7, "Agreed Provision / Term", border=1, align="L", fill=True, new_x="LMARGIN", new_y="NEXT")

            # Table Rows
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(33, 37, 41)
            for idx, item in enumerate(parsed_terms, 1):
                fill_color = 248 if idx % 2 == 1 else 255
                pdf.set_fill_color(fill_color, fill_color, fill_color)

                # Compute height required for multi-cell
                clean_item = _sanitize_for_pdf(item)
                pdf.cell(15, 7, str(idx), border=1, align="C", fill=True)
                pdf.multi_cell(155, 7, clean_item, border=1, align="L", fill=True, new_x="LMARGIN", new_y="NEXT")

            pdf.ln(6)

    # 6. Content Body
    raw_lines = content.split("\n")

    for line in raw_lines:
        trimmed = line.strip()
        if not trimmed:
            pdf.ln(2)
            continue

        clean_line = _sanitize_for_pdf(trimmed)

        # Headings Level 1 (# or SECTION ... / ARTICLE ...)
        if clean_line.startswith("# ") or re.match(r"^(SECTION|ARTICLE)\s+[0-9IVXLCDM]+", clean_line, re.IGNORECASE):
            text = re.sub(r"^#+\s*", "", clean_line)
            pdf.ln(4)
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(15, 34, 64)
            pdf.cell(0, 7, text, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)
            continue

        # Headings Level 2 (## or 1.1 ...)
        if clean_line.startswith("## ") or re.match(r"^\d+\.\d+\s+[A-Z]", clean_line):
            text = re.sub(r"^#+\s*", "", clean_line)
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 10.5)
            pdf.set_text_color(30, 50, 80)
            pdf.cell(0, 6, text, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)
            continue

        # Headings Level 3 (###)
        if clean_line.startswith("### "):
            text = re.sub(r"^#+\s*", "", clean_line)
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 9.5)
            pdf.set_text_color(40, 60, 90)
            pdf.cell(0, 5, text, new_x="LMARGIN", new_y="NEXT")
            continue

        # Bullet points
        if clean_line.startswith("* ") or clean_line.startswith("- "):
            bullet_text = clean_line[2:].strip()
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(33, 37, 41)
            # Indented bullet
            pdf.cell(6, 5, chr(149), align="R")  # bullet dot
            pdf.multi_cell(164, 5, " " + bullet_text, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)
            continue

        # Signature sections
        if any(sig in clean_line.upper() for sig in ["SIGNATURES", "IN WITNESS WHEREOF"]):
            pdf.ln(5)
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(15, 34, 64)
            pdf.cell(0, 7, clean_line.replace("#", "").strip(), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
            continue

        # Standard Paragraph
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(33, 37, 41)
        # Strip simple bold markdown marks for clean rendering
        formatted_paragraph = re.sub(r"\*\*(.*?)\*\*", r"\1", clean_line)
        pdf.multi_cell(0, 5.2, formatted_paragraph, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    # Return output bytes
    return bytes(pdf.output())
