"""LegalEase - API and Endpoint Unit Tests.

Mocks external Gemini API calls and tests FastAPI endpoints thoroughly.
"""

from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import pytest

from ai_core.gemini_generator import GeminiGenerationError
from main import app

client = TestClient(app)

MOCK_LEGAL_CONTRACT = """# EMPLOYMENT AGREEMENT

This Employment Agreement is entered into on January 15, 2026.

SECTION 1. POSITION AND DUTIES
The Employee shall serve as Senior Software Architect.

SECTION 2. COMPENSATION
The Employee shall receive an annual base salary of $165,000 paid bi-weekly.

SECTION 3. CONFIDENTIALITY
The Employee covenants not to disclose any trade secrets.

SECTION 4. SIGNATURES
IN WITNESS WHEREOF, the parties hereto have executed this Agreement.
Employer: Apex Innovations Inc.
Employee: Alex Vance
"""


def test_root_endpoint():
    """Tests the health check root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["application"] == "LegalEase"
    assert "version" in data


def test_generate_endpoint_success():
    """Tests successful document generation with mocked Gemini API."""
    payload = {
        "document_type": "Employment Contract",
        "parties": "Apex Innovations Inc. (Employer)\nAlex Vance (Employee)",
        "terms": "Salary $165,000; 30 days notice; Confidentiality required.",
        "effective_date": "2026-01-15",
        "company_name": "Apex Innovations Inc.",
        "preferred_title": "EXECUTIVE EMPLOYMENT AGREEMENT",
        "footer_text": "Confidential - Apex Innovations",
        "jurisdiction": "State of California, USA",
    }

    with patch("ai_core.gemini_generator.GeminiGenerator.generate_document", return_value=MOCK_LEGAL_CONTRACT):
        response = client.post("/generate", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["document_type"] == "Employment Contract"
    assert data["title"] == "EXECUTIVE EMPLOYMENT AGREEMENT"
    assert "EMPLOYMENT AGREEMENT" in data["content"]
    assert len(data["parsed_terms"]) == 3
    assert data["parsed_terms"][0] == "Salary $165,000"


def test_generate_endpoint_validation_failures():
    """Tests validation errors on missing or empty required fields."""
    # Empty parties
    invalid_payload = {
        "document_type": "Employment Contract",
        "parties": "",
        "terms": "Some terms",
        "effective_date": "2026-01-15",
    }
    response = client.post("/generate", json=invalid_payload)
    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["success"] is False
    assert any("parties" in err.lower() for err in data["detail"]["errors"])

    # Empty terms
    invalid_payload_2 = {
        "document_type": "Employment Contract",
        "parties": "Alice and Bob",
        "terms": "",
        "effective_date": "2026-01-15",
    }
    response = client.post("/generate", json=invalid_payload_2)
    assert response.status_code == 400
    assert any("terms" in err.lower() for err in response.json()["detail"]["errors"])


def test_generate_endpoint_gemini_failure():
    """Tests graceful handling when Gemini API fails."""
    payload = {
        "document_type": "NDA",
        "parties": "Discloser and Recipient",
        "terms": "Strict confidentiality",
        "effective_date": "2026-01-15",
    }

    with patch(
        "ai_core.gemini_generator.GeminiGenerator.generate_document",
        side_effect=GeminiGenerationError("Invalid Gemini API key."),
    ):
        response = client.post("/generate", json=payload)

    assert response.status_code == 502
    data = response.json()
    assert data["detail"]["success"] is False
    assert "Invalid Gemini API key" in data["detail"]["error"]


def test_export_endpoints():
    """Tests the document export REST endpoints."""
    export_payload = {
        "content": MOCK_LEGAL_CONTRACT,
        "title": "Employment Contract",
        "document_type": "Employment Contract",
        "company_name": "Apex Innovations",
        "effective_date": "2026-01-15",
        "terms": "Salary $165,000; 30 days notice",
        "include_terms_table": True,
    }

    # Test TXT Export
    resp_txt = client.post("/export/txt", json=export_payload)
    assert resp_txt.status_code == 200
    assert "text/plain" in resp_txt.headers["content-type"]
    assert b"Apex Innovations" in resp_txt.content

    # Test DOCX Export
    resp_docx = client.post("/export/docx", json=export_payload)
    assert resp_docx.status_code == 200
    assert "wordprocessingml" in resp_docx.headers["content-type"]
    assert len(resp_docx.content) > 1000

    # Test PDF Export
    resp_pdf = client.post("/export/pdf", json=export_payload)
    assert resp_pdf.status_code == 200
    assert "application/pdf" in resp_pdf.headers["content-type"]
    assert resp_pdf.content.startswith(b"%PDF")
