"""LegalEase - DOCX Document Generator.

Generates beautifully formatted, professional Microsoft Word (.docx) legal documents
using python-docx, including headings, terms tables, logos, and signature blocks.
"""

from io import BytesIO
import re
from typing import List, Optional

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

from utils.sanitizer import parse_terms_list


def _set_cell_background(cell, hex_color: str):
    """Sets background color of a table cell in hex format (e.g. 'F0F4F8')."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def _set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Sets cell padding in dxa (1 pt = 20 dxa)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for side, val in [("top", top), ("bottom", bottom), ("left", left), ("right", right)]:
        node = OxmlElement(f"w:{side}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


def generate_docx_bytes(
    content: str,
    title: Optional[str] = None,
    company_name: Optional[str] = None,
    effective_date: Optional[str] = None,
    footer_text: Optional[str] = None,
    logo_bytes: Optional[bytes] = None,
    terms: Optional[str] = None,
    include_terms_table: bool = True,
) -> bytes:
    """Generates a styled .docx legal document as bytes."""
    doc = Document()

    # Set 1-inch margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

        # Configure Header & Footer
        footer = section.footer
        f_p = footer.paragraphs[0]
        f_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        f_run = f_p.add_run(footer_text.strip() if footer_text else "LegalEase - Confidential Legal Document")
        f_run.font.name = "Times New Roman"
        f_run.font.size = Pt(8.5)
        f_run.font.italic = True
        f_run.font.color.rgb = RGBColor(120, 120, 120)

    # Styles Setup
    normal_style = doc.styles["Normal"]
    normal_style.font.name = "Times New Roman"
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = RGBColor(33, 37, 41)
    normal_style.paragraph_format.line_spacing = 1.15
    normal_style.paragraph_format.space_after = Pt(6)

    # 1. Company Logo
    if logo_bytes:
        try:
            logo_stream = BytesIO(logo_bytes)
            p_logo = doc.add_paragraph()
            p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_logo.paragraph_format.space_after = Pt(12)
            run_logo = p_logo.add_run()
            run_logo.add_picture(logo_stream, width=Inches(1.8))
        except Exception:
            pass  # Fallback gracefully if image cannot be parsed

    # 2. Company Name
    if company_name and company_name.strip():
        p_comp = doc.add_paragraph()
        p_comp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_comp.paragraph_format.space_after = Pt(2)
        r_comp = p_comp.add_run(company_name.strip().upper())
        r_comp.font.name = "Times New Roman"
        r_comp.font.size = Pt(11)
        r_comp.font.bold = True
        r_comp.font.color.rgb = RGBColor(70, 80, 95)

    # 3. Document Title
    doc_title = title.strip() if title and title.strip() else "LEGAL AGREEMENT"
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(6)
    p_title.paragraph_format.space_after = Pt(8)
    r_title = p_title.add_run(doc_title.upper())
    r_title.font.name = "Times New Roman"
    r_title.font.size = Pt(18)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(15, 34, 64)  # Deep Navy

    # 4. Effective Date Subtitle
    if effective_date and effective_date.strip():
        p_date = doc.add_paragraph()
        p_date.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_date.paragraph_format.space_after = Pt(16)
        r_date = p_date.add_run(f"Effective Date: {effective_date.strip()}")
        r_date.font.name = "Times New Roman"
        r_date.font.size = Pt(10.5)
        r_date.font.italic = True
        r_date.font.color.rgb = RGBColor(90, 100, 110)

    # 5. Terms Table (if requested and terms provided)
    if include_terms_table and terms:
        parsed_terms = parse_terms_list(terms)
        if len(parsed_terms) > 1:
            p_table_head = doc.add_paragraph()
            p_table_head.paragraph_format.space_before = Pt(12)
            p_table_head.paragraph_format.space_after = Pt(4)
            r_th = p_table_head.add_run("KEY TERMS & PROVISIONS SUMMARY")
            r_th.font.name = "Times New Roman"
            r_th.font.size = Pt(12)
            r_th.font.bold = True
            r_th.font.color.rgb = RGBColor(15, 34, 64)

            table = doc.add_table(rows=1, cols=2)
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            table.autofit = False

            # Set column widths
            table.columns[0].width = Inches(0.8)
            table.columns[1].width = Inches(5.7)

            # Header Row
            hdr_cells = table.rows[0].cells
            hdr_cells[0].text = "No."
            hdr_cells[1].text = "Agreed Term / Specification"
            for c in hdr_cells:
                _set_cell_background(c, "E2E8F0")
                _set_cell_margins(c, 120, 120, 150, 150)
                p = c.paragraphs[0]
                for r in p.runs:
                    r.font.name = "Times New Roman"
                    r.font.size = Pt(10)
                    r.font.bold = True
                    r.font.color.rgb = RGBColor(15, 34, 64)

            # Data Rows
            for idx, item in enumerate(parsed_terms, 1):
                row_cells = table.add_row().cells
                row_cells[0].text = str(idx)
                row_cells[1].text = item
                bg = "F8FAFC" if idx % 2 == 1 else "FFFFFF"
                for i, c in enumerate(row_cells):
                    _set_cell_background(c, bg)
                    _set_cell_margins(c, 100, 100, 150, 150)
                    p = c.paragraphs[0]
                    if i == 0:
                        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for r in p.runs:
                        r.font.name = "Times New Roman"
                        r.font.size = Pt(10)

            doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # 6. Parse Content Body
    raw_lines = content.split("\n")
    in_signature_section = False

    for line in raw_lines:
        trimmed = line.strip()

        if not trimmed:
            continue

        # Check for signature header
        if any(sig_kw in trimmed.upper() for sig_kw in ["SIGNATURES", "IN WITNESS WHEREOF", "SIGNATURE PAGE"]):
            in_signature_section = True
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(16)
            p.paragraph_format.space_after = Pt(8)
            r = p.add_run(trimmed.replace("#", "").strip())
            r.font.name = "Times New Roman"
            r.font.size = Pt(13)
            r.font.bold = True
            r.font.color.rgb = RGBColor(15, 34, 64)
            continue

        # Headings Level 1 (# or SECTION ... / ARTICLE ...)
        if trimmed.startswith("# ") or re.match(r"^(SECTION|ARTICLE)\s+[0-9IVXLCDM]+", trimmed, re.IGNORECASE):
            text = re.sub(r"^#+\s*", "", trimmed)
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(4)
            r = p.add_run(text)
            r.font.name = "Times New Roman"
            r.font.size = Pt(13)
            r.font.bold = True
            r.font.color.rgb = RGBColor(15, 34, 64)
            continue

        # Headings Level 2 (## or 1.1 / Section 1.1)
        if trimmed.startswith("## ") or re.match(r"^\d+\.\d+\s+[A-Z]", trimmed):
            text = re.sub(r"^#+\s*", "", trimmed)
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(3)
            r = p.add_run(text)
            r.font.name = "Times New Roman"
            r.font.size = Pt(11.5)
            r.font.bold = True
            r.font.color.rgb = RGBColor(30, 50, 80)
            continue

        # Headings Level 3 (###)
        if trimmed.startswith("### "):
            text = re.sub(r"^#+\s*", "", trimmed)
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(text)
            r.font.name = "Times New Roman"
            r.font.size = Pt(11)
            r.font.bold = True
            r.font.italic = True
            r.font.color.rgb = RGBColor(40, 60, 90)
            continue

        # Bullets
        if re.match(r"^[-*•]\s+", trimmed):
            text = re.sub(r"^[-*•]\s+", "", trimmed)
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.space_after = Pt(4)
            r = p.add_run(text)
            r.font.name = "Times New Roman"
            r.font.size = Pt(11)
            continue

        # Standard Paragraph
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(6)

        # Format inline bold markings like **text**
        parts = re.split(r"(\*\*.*?\*\*)", trimmed)
        for part in parts:
            if part.startswith("**") and part.endswith("**") and len(part) >= 4:
                bold_text = part[2:-2]
                r = p.add_run(bold_text)
                r.font.name = "Times New Roman"
                r.font.size = Pt(11)
                r.font.bold = True
            else:
                r = p.add_run(part)
                r.font.name = "Times New Roman"
                r.font.size = Pt(11)

    # Save to buffer
    output_stream = BytesIO()
    doc.save(output_stream)
    return output_stream.getvalue()
