# LegalEase – AI-Powered Legal Document Generator

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red.svg)](https://streamlit.io/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-SDK%201.0+-orange.svg)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

**LegalEase** is a polished, enterprise-ready legal document generator that helps individuals and businesses draft, preview, edit, and export structured legal agreements using Google Gemini.

---

## 🌟 Key Features

1. **Document Classification**: Pre-configured templates for Employment Contracts, Offer Letters, NDAs, Lease Agreements, Freelance Contracts, Service Agreements, General Contracts, and custom agreements.
2. **AI-Powered Legal Drafting**: Generates formal, legally structured clauses using Google Gemini with specialized prompt engineering.
3. **Interactive Document Editor**: Real-time editable document view enabling users to refine, rewrite, or add custom clauses before exporting.
4. **Multi-Format Export**:
   - **TXT**: Clean UTF-8 text file.
   - **DOCX**: Formatted Microsoft Word document with custom typography, 1-inch margins, terms summary table, company logo, and signature lines.
   - **PDF**: Formal multi-page A4 PDF layout with header branding, page numbering ("Page X of Y"), terms summary table, and footers.
5. **Structured Terms Table**: Automatically parses semicolon- or newline-separated terms and renders an executive summary table across previews and downloads.
6. **Enterprise Branding**: Upload company logo, specify organization names, custom document titles, and confidential footer tags.
7. **Legal Safety Disclaimer**: Prominent notices ensuring drafts are used for informational purposes and reviewed by qualified legal counsel.
8. **Decoupled Architecture**: High-performance FastAPI REST backend with a modern, responsive Streamlit frontend.

---

## 🏗️ Architecture & Technology Stack

- **Frontend**: Streamlit with custom CSS (responsive cards, paper layout preview, tabs, and interactive validation).
- **Backend**: FastAPI, Uvicorn, Pydantic v2 (validation & serialization).
- **AI Core**: Google Gemini SDK (`google-genai` / `google-generativeai`) with configurable models and fallback resilience.
- **Document Exporters**:
  - `python-docx` for Word documents (.docx)
  - `fpdf2` for printable PDFs (.pdf)
  - Python standard library for plain text (.txt)
  - `Pillow` for logo validation and processing

---

## 📁 Project Directory Structure

```text
LegalEase/
│
├── app.py                      # Streamlit frontend web application
├── main.py                     # FastAPI application entry point
├── routes.py                   # REST API routes & endpoints (/generate, /export/*)
├── requirements.txt            # Python dependencies
├── .env.example                # Sample environment variables
├── .env                        # Local environment configuration
├── Dockerfile                  # Container definition for production deployment
├── README.md                   # Documentation and user manual
│
├── ai_core/
│   ├── __init__.py
│   └── gemini_generator.py     # Gemini client, prompt engineering & fallbacks
│
├── generators/
│   ├── __init__.py
│   ├── txt_generator.py        # Plain text document generator
│   ├── docx_generator.py       # Microsoft Word (.docx) generator with styling
│   └── pdf_generator.py        # A4 PDF generator with multi-page flow
│
├── utils/
│   ├── __init__.py
│   ├── sanitizer.py            # Filename, HTML, and text sanitizers
│   └── validators.py           # Form and logo file upload validators
│
├── assets/
│   └── logo.png                # Official LegalEase branding asset
│
└── tests/
    ├── __init__.py
    ├── test_api.py             # API and endpoint tests (mocking Gemini)
    └── test_generators.py      # Format generators and utility tests
```

---

## ⚙️ Installation & Setup

### 1. Prerequisites
- Python 3.10+ (Python 3.11 recommended)
- A Google Gemini API key from [Google AI Studio](https://aistudio.google.com/)

### 2. Clone and Setup Environment
```bash
# Navigate to the project directory
cd "c:/Users/DELL/Desktop/new folder"

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows Command Prompt:
.\venv\Scripts\activate.bat
# Linux / macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your Gemini API key:
```bash
cp .env.example .env
```
Inside `.env`:
```ini
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-3.8-flash
BACKEND_URL=http://localhost:8000
HOST=0.0.0.0
PORT=8000
```

---

## 🚀 Running the Application

### Option A: Run Locally (Recommended)

#### Terminal 1 — Start the FastAPI Backend:
```bash
uvicorn main:app --reload --port 8000
```
- API Documentation (Swagger UI): [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/](http://localhost:8000/)

#### Terminal 2 — Start the Streamlit Frontend:
```bash
streamlit run app.py
```
- Frontend UI: [http://localhost:8501](http://localhost:8501)

---

### Option B: Run via Docker

```bash
# Build the Docker image
docker build -t legalease .

# Run the container (maps ports 8000 and 8501)
docker run -p 8000:8000 -p 8501:8501 --env-file .env legalease
```

---

## 🧪 Running Automated Tests

Run the complete pytest test suite:
```bash
pytest -v
```

The test suite covers:
- Root API endpoint (`GET /`)
- Document generation endpoint (`POST /generate`)
- Bad request and validation errors
- Gemini API failure simulation
- TXT, DOCX, and PDF exporters
- Text, HTML, and filename sanitization
- Semicolon-delimited terms parsing
- Logo file upload validation

---

## 📖 Walkthrough: Generating a Document

1. **Select Document Type**: Choose from the dropdown (e.g. *Employment Contract*, *Non-Disclosure Agreement*, *Lease Agreement*, or *Other*).
2. **Enter Parties**: Specify the entities or individuals involved (e.g., `Employer: Acme Corp`, `Employee: Jane Doe`).
3. **Specify Terms & Conditions**: Enter agreed terms separated by semicolons (`;`) or line breaks.
4. **Choose Effective Date**: Select the date from the date picker.
5. **(Optional) Add Branding**: Expand *Professional Branding & Advanced Options* to add an organization name, governing jurisdiction, custom footer, or upload a company logo.
6. **Generate**: Click **⚡ Generate Legal Document**.
7. **Preview & Edit**:
   - Review the generated agreement in the authentic paper-styled preview.
   - Click **✏️ Edit Document** to modify any section directly, then click **💾 Save Changes**.
8. **Export**: Click **Download TXT**, **Download DOCX**, or **Download PDF** to export your updated agreement.

---

## ⚖️ Legal Disclaimer

> **Important:** LegalEase provides AI-generated legal information and document drafts for informational purposes only. It does not constitute legal advice and does not create an attorney-client relationship. All generated documents should be reviewed by a licensed attorney before execution.
