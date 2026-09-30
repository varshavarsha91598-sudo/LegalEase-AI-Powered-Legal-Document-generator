"""LegalEase - FastAPI Routes.

Defines API endpoints for health check, AI legal document generation, and document export.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel, Field

from ai_core.gemini_generator import GeminiGenerationError, GeminiGenerator
from generators.docx_generator import generate_docx_bytes
from generators.pdf_generator import generate_pdf_bytes
from generators.txt_generator import generate_txt_bytes
from utils.sanitizer import clean_legal_text, parse_terms_list, sanitize_filename
from utils.validators import validate_document_request

router = APIRouter()


class DocumentRequest(BaseModel):
    document_type: str = Field(..., description="Type of legal document (e.g. Non-Disclosure Agreement)")
    parties: str = Field(..., description="Names and roles of the parties involved")
    terms: str = Field(..., description="Agreed terms, provisions, or specifications")
    effective_date: str = Field(..., description="Effective date of the agreement")
    company_name: Optional[str] = Field(None, description="Optional company or organization name")
    preferred_title: Optional[str] = Field(None, description="Optional custom document title")
    footer_text: Optional[str] = Field(None, description="Optional custom footer text")
    jurisdiction: Optional[str] = Field(None, description="Optional governing jurisdiction")


class DocumentResponse(BaseModel):
    success: bool = True
    document_type: str
    title: str
    content: str
    parsed_terms: List[str]
    effective_date: str


class ExportRequest(BaseModel):
    content: str
    title: Optional[str] = "Legal Agreement"
    document_type: Optional[str] = "Document"
    company_name: Optional[str] = None
    effective_date: Optional[str] = None
    footer_text: Optional[str] = None
    terms: Optional[str] = None
    include_terms_table: Optional[bool] = True


@router.post("/generate", response_model=DocumentResponse)
def generate_document_endpoint(payload: DocumentRequest):
    """Generates a formal legal document from user parameters using Google Gemini."""
    # 1. Validate inputs
    is_valid, error_messages = validate_document_request(
        document_type=payload.document_type,
        parties=payload.parties,
        terms=payload.terms,
        effective_date=payload.effective_date,
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "errors": error_messages},
        )

    # 2. Call Gemini Document Generator
    generator = GeminiGenerator()
    try:
        content = generator.generate_document(
            document_type=payload.document_type,
            parties=payload.parties,
            terms=payload.terms,
            effective_date=payload.effective_date,
            company_name=payload.company_name,
            preferred_title=payload.preferred_title,
            jurisdiction=payload.jurisdiction,
        )
    except GeminiGenerationError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"success": False, "error": str(e)},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "An unexpected error occurred while generating the document. Please try again later.",
            },
        )

    # 3. Sanitize and structure response
    sanitized_content = clean_legal_text(content)
    parsed_terms = parse_terms_list(payload.terms)
    doc_title = payload.preferred_title or payload.document_type

    return DocumentResponse(
        success=True,
        document_type=payload.document_type,
        title=doc_title,
        content=sanitized_content,
        parsed_terms=parsed_terms,
        effective_date=payload.effective_date,
    )


@router.post("/export/txt")
def export_txt_endpoint(payload: ExportRequest):
    """Exports document content as a plain text file."""
    txt_bytes = generate_txt_bytes(
        content=payload.content,
        title=payload.title,
        company_name=payload.company_name,
        footer_text=payload.footer_text,
    )
    filename = sanitize_filename(payload.title or payload.document_type or "Document", ext="txt")
    return Response(
        content=txt_bytes,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/export/docx")
def export_docx_endpoint(payload: ExportRequest):
    """Exports document content as a Microsoft Word (.docx) document."""
    docx_bytes = generate_docx_bytes(
        content=payload.content,
        title=payload.title,
        company_name=payload.company_name,
        effective_date=payload.effective_date,
        footer_text=payload.footer_text,
        terms=payload.terms,
        include_terms_table=bool(payload.include_terms_table),
    )
    filename = sanitize_filename(payload.title or payload.document_type or "Document", ext="docx")
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/export/pdf")
def export_pdf_endpoint(payload: ExportRequest):
    """Exports document content as an A4 legal PDF document."""
    pdf_bytes = generate_pdf_bytes(
        content=payload.content,
        title=payload.title,
        company_name=payload.company_name,
        effective_date=payload.effective_date,
        footer_text=payload.footer_text,
        terms=payload.terms,
        include_terms_table=bool(payload.include_terms_table),
    )
    filename = sanitize_filename(payload.title or payload.document_type or "Document", ext="pdf")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
