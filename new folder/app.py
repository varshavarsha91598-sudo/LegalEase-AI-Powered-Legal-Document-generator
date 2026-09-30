"""LegalEase – AI-Powered Legal Document Generator.

Professional Streamlit Frontend for generating, previewing, editing,
and exporting legal contracts with Google Gemini.
"""

from datetime import date
from io import BytesIO
import os
from pathlib import Path
import re
from typing import Dict, List, Optional
import requests
import streamlit as st
from PIL import Image

# Internal modules
from ai_core.gemini_generator import GeminiGenerationError, GeminiGenerator
from generators.docx_generator import generate_docx_bytes
from generators.pdf_generator import generate_pdf_bytes
from generators.txt_generator import generate_txt_bytes
from utils.sanitizer import clean_legal_text, parse_terms_list, sanitize_filename, sanitize_html
from utils.validators import validate_document_request, validate_logo_file

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
ASSETS_DIR = Path(__file__).parent / "assets"
LOGO_PATH = ASSETS_DIR / "logo.png"

# Page Configuration
st.set_page_config(
    page_title="LegalEase – AI-Powered Legal Document Generator",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling (Professional Legal / SaaS aesthetic)
st.markdown(
    """
<style>
    /* Global Styles & Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Playfair+Display:wght@600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        --primary-navy: #0F172A;
        --secondary-navy: #1E293B;
        --accent-blue: #2563EB;
        --accent-gold: #D97706;
        --light-bg: #F8FAFC;
        --border-color: #E2E8F0;
        --text-dark: #0F172A;
        --text-muted: #64748B;
    }

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Main Container Padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 4rem;
        max-width: 1200px;
    }

    /* Header & Hero */
    .hero-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #1E3A8A 100%);
        padding: 2.2rem 2.5rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.25);
        border: 1px solid rgba(255, 255, 255, 0.1);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .hero-title {
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 2.4rem;
        font-weight: 700;
        letter-spacing: -0.5px;
        margin: 0;
        color: #FFFFFF;
    }
    .hero-subtitle {
        font-size: 1.05rem;
        color: #93C5FD;
        margin-top: 0.35rem;
        font-weight: 400;
    }
    .hero-badge {
        background: rgba(217, 119, 6, 0.2);
        border: 1px solid #F59E0B;
        color: #FCD34D;
        padding: 0.35rem 0.85rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }

    /* Legal Disclaimer Banner */
    .disclaimer-box {
        background-color: #FEF3C7;
        border-left: 4px solid #D97706;
        padding: 0.85rem 1.25rem;
        border-radius: 8px;
        color: #92400E;
        font-size: 0.85rem;
        line-height: 1.45;
        margin-bottom: 1.75rem;
    }

    /* Card Containers */
    .form-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
        margin-bottom: 1.5rem;
    }

    /* Document Paper Style Preview */
    .document-paper {
        background: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-radius: 8px;
        padding: 3rem 3.5rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
        color: #1E293B;
        font-family: 'Times New Roman', Times, serif;
        font-size: 1.05rem;
        line-height: 1.65;
        max-height: 750px;
        overflow-y: auto;
    }
    .document-paper h1, .document-paper h2, .document-paper h3 {
        font-family: 'Times New Roman', Times, serif;
        color: #0F172A;
    }
    .document-paper hr {
        border-color: #E2E8F0;
    }

    /* Terms Table in Preview */
    .preview-terms-table {
        width: 100%;
        border-collapse: collapse;
        margin: 1.25rem 0;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.9rem;
    }
    .preview-terms-table th {
        background-color: #F1F5F9;
        color: #0F172A;
        font-weight: 600;
        text-align: left;
        padding: 8px 12px;
        border: 1px solid #CBD5E1;
    }
    .preview-terms-table td {
        padding: 8px 12px;
        border: 1px solid #E2E8F0;
        color: #334155;
    }
    .preview-terms-table tr:nth-child(even) {
        background-color: #F8FAFC;
    }

    /* Primary Buttons */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
    }

    /* Download Cards */
    .download-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1.2rem;
        text-align: center;
        transition: transform 0.15s ease;
    }
    .download-card:hover {
        border-color: #3B82F6;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.08);
    }
</style>
""",
    unsafe_allow_html=True,
)

# Preset scenario templates for quick testing
SAMPLE_TEMPLATES = {
    "Select a pre-filled template...": None,
    "💼 Scenario 1: Employment Contract": {
        "document_type": "Employment Contract",
        "title": "EXECUTIVE EMPLOYMENT AGREEMENT",
        "company_name": "Apex Innovations Inc.",
        "parties": "Apex Innovations Inc., a Delaware corporation (Employer)\nAlex Vance, an individual residing in California (Employee)",
        "terms": "Job Title: Senior Software Architect;\nAnnual Base Salary: $165,000 paid bi-weekly;\nStandard 40-hour work week with remote work flexibility;\nConfidentiality: Strict non-disclosure of proprietary source code and client data during and after employment;\nIntellectual Property: All inventions, code, and works created during employment belong exclusively to Employer;\nTermination: Either party may terminate with 30 days written notice, or immediately for cause;\nBenefits: Full health insurance, 401(k) with 4% match, and 20 days PTO annually.",
        "jurisdiction": "State of California, USA",
        "footer_text": "Confidential - Apex Innovations Inc. Employment Agreement",
    },
    "🔒 Scenario 2: Non-Disclosure Agreement (NDA)": {
        "document_type": "Non-Disclosure Agreement (NDA)",
        "title": "MUTUAL NON-DISCLOSURE AGREEMENT",
        "company_name": "TechNova Solutions Ltd.",
        "parties": "TechNova Solutions Ltd. (Disclosing Party)\nSarah Jenkins, Independent Consultant (Receiving Party)",
        "terms": "Scope of Confidentiality: Technical architectures, business strategies, API keys, and customer records;\nPermitted Use: Solely for evaluating a prospective joint technology partnership;\nNon-Disclosure Obligation: Receiving party must exercise highest reasonable standard of care;\nPermitted Disclosure: Only to direct employees or legal counsel on a need-to-know basis under equivalent confidentiality agreements;\nDuration of Obligation: 3 years from the date of disclosure;\nReturn of Materials: All confidential documents and copies must be returned or destroyed within 7 days upon written demand;\nInjunctive Relief: Breach entitles Disclosing Party to seek immediate court injunction without posting bond.",
        "jurisdiction": "State of New York, USA",
        "footer_text": "TechNova Solutions Ltd. - Proprietary & Confidential",
    },
    "🏠 Scenario 3: Lease Agreement": {
        "document_type": "Lease Agreement",
        "title": "RESIDENTIAL LEASE AGREEMENT",
        "company_name": "Skyline Property Management",
        "parties": "Skyline Property Management LLC (Landlord)\nMarcus Sterling and Elena Sterling (Tenants)",
        "terms": "Premises: Apartment 4B, 742 Evergreen Terrace, Springfield;\nTerm: 12-month fixed lease commencing on the effective date;\nMonthly Rent: $2,400 due on the first day of each calendar month via direct transfer;\nSecurity Deposit: $2,400 deposited in an escrow account, refundable within 21 days of lease end subject to damages inspection;\nUtilities: Tenant pays electricity, gas, and internet; Landlord covers water, sewer, and trash collection;\nOccupancy & Pets: No unauthorized sub-leasing; pets allowed upon approval and payment of a $300 pet deposit;\nTermination: 60 days advance written notice required prior to lease expiration for renewal or surrender.",
        "jurisdiction": "Commonwealth of Massachusetts, USA",
        "footer_text": "Skyline Property Management - Official Lease Agreement",
    },
}


def check_backend_health() -> bool:
    """Checks whether the FastAPI backend server is accessible."""
    try:
        resp = requests.get(f"{BACKEND_URL}/", timeout=1.5)
        return resp.status_code == 200 and resp.json().get("status") == "ok"
    except Exception:
        return False


def call_generate_api(
    document_type: str,
    parties: str,
    terms: str,
    effective_date_str: str,
    company_name: Optional[str],
    preferred_title: Optional[str],
    footer_text: Optional[str],
    jurisdiction: Optional[str],
) -> Dict:
    """Invokes backend /generate API, with local fallback if backend is offline."""
    payload = {
        "document_type": document_type,
        "parties": parties,
        "terms": terms,
        "effective_date": effective_date_str,
        "company_name": company_name,
        "preferred_title": preferred_title,
        "footer_text": footer_text,
        "jurisdiction": jurisdiction,
    }

    try:
        response = requests.post(f"{BACKEND_URL}/generate", json=payload, timeout=60)
        if response.status_code == 200:
            return response.json()
        else:
            err_data = response.json()
            err_detail = err_data.get("detail", {})
            if isinstance(err_detail, dict) and "error" in err_detail:
                raise Exception(err_detail["error"])
            elif isinstance(err_detail, dict) and "errors" in err_detail:
                raise Exception(", ".join(err_detail["errors"]))
            else:
                raise Exception(f"Backend error ({response.status_code}): {response.text}")
    except requests.exceptions.ConnectionError:
        # Backend is not running; fallback to direct GeminiGenerator
        st.warning("Backend API is currently offline. Falling back to direct AI generation.")
        generator = GeminiGenerator()
        content = generator.generate_document(
            document_type=document_type,
            parties=parties,
            terms=terms,
            effective_date=effective_date_str,
            company_name=company_name,
            preferred_title=preferred_title,
            jurisdiction=jurisdiction,
        )
        return {
            "success": True,
            "document_type": document_type,
            "title": preferred_title or document_type,
            "content": clean_legal_text(content),
            "parsed_terms": parse_terms_list(terms),
            "effective_date": effective_date_str,
        }


# Session State Initialization
if "generated_document" not in st.session_state:
    st.session_state.generated_document = None
if "edited_document" not in st.session_state:
    st.session_state.edited_document = ""
if "doc_title" not in st.session_state:
    st.session_state.doc_title = "Legal Agreement"
if "doc_type" not in st.session_state:
    st.session_state.doc_type = "Contract"
if "parsed_terms" not in st.session_state:
    st.session_state.parsed_terms = []
if "is_editing" not in st.session_state:
    st.session_state.is_editing = False
if "company_name" not in st.session_state:
    st.session_state.company_name = ""
if "footer_text" not in st.session_state:
    st.session_state.footer_text = ""
if "effective_date" not in st.session_state:
    st.session_state.effective_date = str(date.today())
if "logo_bytes" not in st.session_state:
    st.session_state.logo_bytes = None
if "include_table" not in st.session_state:
    st.session_state.include_table = True

# --- SIDEBAR ---
with st.sidebar:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=160)
    else:
        st.title("⚖️ LegalEase")

    st.markdown("### AI Legal Document Generator")
    st.markdown(
        "Generate formal, structured contracts and agreements in seconds powered by Google Gemini."
    )

    st.divider()

    # Backend Connection Status
    backend_online = check_backend_health()
    if backend_online:
        st.success("🟢 Backend API: Online (Port 8000)")
    else:
        st.info("🟡 Backend API: Offline (Direct AI mode active)")

    st.divider()

    # Quick Fill Templates
    st.markdown("#### ⚡ Quick-Fill Scenarios")
    selected_template_key = st.selectbox(
        "Load sample data for testing:",
        options=list(SAMPLE_TEMPLATES.keys()),
        index=0,
    )

    st.divider()

    # Supported Document Types
    st.markdown("#### 📋 Supported Document Types")
    st.caption(
        "• Employment Contracts & Offer Letters\n"
        "• Non-Disclosure Agreements (NDAs)\n"
        "• Residential & Commercial Leases\n"
        "• Freelance & Consulting Contracts\n"
        "• Service Agreements\n"
        "• Business & Partnership Agreements\n"
        "• Custom Legal Documents"
    )

    st.divider()

    # Legal Disclaimer
    st.markdown("#### ⚖️ Legal Safety Disclaimer")
    st.caption(
        "LegalEase provides AI-generated legal information and document drafts for informational purposes. "
        "It does not provide legal advice and does not replace review by a qualified legal professional."
    )

# --- HERO SECTION ---
st.markdown(
    """
    <div class="hero-header">
        <div>
            <h1 class="hero-title">LegalEase</h1>
            <div class="hero-subtitle">AI-Powered Enterprise Legal Document Generator</div>
        </div>
        <div>
            <span class="hero-badge">Enterprise v1.0</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Disclaimer Box
st.markdown(
    """
    <div class="disclaimer-box">
        <strong>Important Notice:</strong> LegalEase provides AI-generated legal information and document drafts for informational purposes.
        It does not provide legal advice and does not replace review by a qualified legal professional.
    </div>
    """,
    unsafe_allow_html=True,
)

# Apply Template Selection if chosen
template_data = SAMPLE_TEMPLATES.get(selected_template_key)

# --- MAIN FORM ---
st.markdown("### 📝 Document Parameters")

with st.container():
    col1, col2 = st.columns([1, 1])

    doc_types = [
        "Employment Contract",
        "Employment Offer Letter",
        "Non-Disclosure Agreement (NDA)",
        "Lease Agreement",
        "Freelance Contract",
        "Service Agreement",
        "Business Agreement",
        "General Contract",
        "Other",
    ]

    # Pre-selection logic based on template
    default_type_idx = 0
    if template_data and template_data["document_type"] in doc_types:
        default_type_idx = doc_types.index(template_data["document_type"])

    with col1:
        selected_doc_type = st.selectbox(
            "Document Type *",
            options=doc_types,
            index=default_type_idx,
            help="Select the classification of legal agreement you want to generate.",
        )

        custom_doc_type = ""
        if selected_doc_type == "Other":
            custom_doc_type = st.text_input(
                "Specify Document Type *",
                placeholder="e.g. Intellectual Property Assignment Agreement",
            )

        final_doc_type = custom_doc_type.strip() if selected_doc_type == "Other" else selected_doc_type

        default_parties = template_data["parties"] if template_data else ""
        parties_input = st.text_area(
            "Parties Involved *",
            value=default_parties,
            placeholder="Jane Doe (Service Provider)\nTechNova Inc. (Client)",
            height=140,
            help="Enter all legal parties, entities, and their roles in the agreement.",
        )

    with col2:
        effective_date_val = st.date_input(
            "Effective Date *",
            value=date.today(),
            help="The date from which this agreement shall take legal effect.",
        )

        default_terms = template_data["terms"] if template_data else ""
        terms_input = st.text_area(
            "Agreed Terms & Conditions *",
            value=default_terms,
            placeholder="Payment must be made within 30 days;\nThe provider must deliver the work by the agreed deadline;\nConfidentiality must be maintained;\nEither party may terminate with 15 days notice.",
            height=140,
            help="Enter agreed terms. You can separate multiple terms with semicolons (;) or line breaks.",
        )

    # Helper: Interactive Terms Preview
    if terms_input.strip():
        parsed_live_terms = parse_terms_list(terms_input)
        if parsed_live_terms:
            with st.expander(f"🔍 Detected {len(parsed_live_terms)} Individual Terms (Click to inspect)", expanded=False):
                for idx, t in enumerate(parsed_live_terms, 1):
                    st.markdown(f"**{idx}.** {t}")

    # Optional Branding & Customization Expander
    with st.expander("🏢 Professional Branding & Advanced Options (Optional)", expanded=bool(template_data)):
        brand_col1, brand_col2 = st.columns(2)
        with brand_col1:
            company_name_input = st.text_input(
                "Company / Organization Name",
                value=template_data.get("company_name", "") if template_data else "",
                placeholder="e.g. Apex Innovations Inc.",
            )
            preferred_title_input = st.text_input(
                "Preferred Document Title",
                value=template_data.get("title", "") if template_data else "",
                placeholder="e.g. MASTER SERVICES AGREEMENT",
            )
        with brand_col2:
            jurisdiction_input = st.text_input(
                "Governing Jurisdiction",
                value=template_data.get("jurisdiction", "") if template_data else "",
                placeholder="e.g. State of California, USA",
            )
            footer_text_input = st.text_input(
                "Custom Footer Text",
                value=template_data.get("footer_text", "") if template_data else "",
                placeholder="e.g. Confidential & Proprietary - Apex Innovations",
            )

        brand_col3, brand_col4 = st.columns(2)
        with brand_col3:
            uploaded_logo = st.file_uploader(
                "Upload Company Logo (PNG, JPG, WEBP)",
                type=["png", "jpg", "jpeg", "webp"],
                help="Uploaded logo will be embedded on the first page of DOCX and PDF downloads.",
            )
            logo_data_bytes = None
            if uploaded_logo is not None:
                file_bytes = uploaded_logo.read()
                is_valid_logo, logo_err = validate_logo_file(file_bytes, uploaded_logo.name)
                if is_valid_logo:
                    logo_data_bytes = file_bytes
                    st.image(uploaded_logo, caption="Logo Preview", width=120)
                else:
                    st.error(logo_err)

        with brand_col4:
            st.markdown("<br>", unsafe_allow_html=True)
            include_table_check = st.checkbox(
                "Include Structured Terms Summary Table in DOCX/PDF",
                value=True,
                help="Generates an executive summary table of parsed terms at the start of the document.",
            )

    # Generate Action
    st.markdown("<br>", unsafe_allow_html=True)
    generate_btn = st.button(
        "⚡ Generate Legal Document",
        type="primary",
        use_container_width=True,
    )

if generate_btn:
    # 1. Validation
    is_valid, validation_errors = validate_document_request(
        document_type=final_doc_type,
        parties=parties_input,
        terms=terms_input,
        effective_date=effective_date_val,
    )

    if not is_valid:
        for err in validation_errors:
            st.error(f"⚠️ {err}")
    else:
        with st.spinner("🤖 Google Gemini is analyzing terms and drafting formal legal clauses..."):
            try:
                date_str = effective_date_val.strftime("%B %d, %Y")
                resp = call_generate_api(
                    document_type=final_doc_type,
                    parties=parties_input,
                    terms=terms_input,
                    effective_date_str=date_str,
                    company_name=company_name_input,
                    preferred_title=preferred_title_input,
                    footer_text=footer_text_input,
                    jurisdiction=jurisdiction_input,
                )

                # Update session state
                st.session_state.generated_document = resp.get("content", "")
                st.session_state.edited_document = resp.get("content", "")
                st.session_state.doc_title = resp.get("title", final_doc_type)
                st.session_state.doc_type = final_doc_type
                st.session_state.parsed_terms = resp.get("parsed_terms", [])
                st.session_state.company_name = company_name_input
                st.session_state.footer_text = footer_text_input
                st.session_state.effective_date = date_str
                st.session_state.logo_bytes = logo_data_bytes
                st.session_state.include_table = include_table_check
                st.session_state.is_editing = False

                st.success("✅ Document drafted successfully! Review, edit, or download below.")
            except GeminiGenerationError as e:
                st.error(f"❌ Document Generation Failed: {str(e)}")
            except Exception as e:
                st.error(
                    "❌ Unable to generate the document right now. Please verify your API configuration and try again."
                )
                with st.expander("Diagnostic details"):
                    st.caption(str(e))

# --- PREVIEW & EDIT SECTION ---
if st.session_state.generated_document:
    st.markdown("<br><hr>", unsafe_allow_html=True)
    st.markdown("### 📄 Document Review & Export")

    # Action Toolbar: Toggle Edit / View
    toolbar_col1, toolbar_col2, toolbar_col3 = st.columns([2, 1, 1])
    with toolbar_col1:
        st.markdown(f"#### **{sanitize_html(st.session_state.doc_title)}**")
        st.caption(f"Classification: {st.session_state.doc_type} | Effective Date: {st.session_state.effective_date}")

    with toolbar_col2:
        if st.session_state.is_editing:
            if st.button("👁️ View Preview Mode", use_container_width=True):
                st.session_state.is_editing = False
                st.rerun()
        else:
            if st.button("✏️ Edit Document", use_container_width=True):
                st.session_state.is_editing = True
                st.rerun()

    with toolbar_col3:
        if st.button("🔄 Reset to AI Draft", use_container_width=True):
            st.session_state.edited_document = st.session_state.generated_document
            st.success("Reset document to original AI draft.")
            st.rerun()

    # EDITING MODE
    if st.session_state.is_editing:
        st.info("💡 You are in **Editor Mode**. Make any required adjustments, clause modifications, or additions.")
        user_edited_text = st.text_area(
            "Document Editor",
            value=st.session_state.edited_document,
            height=550,
            label_visibility="collapsed",
        )

        edit_save_col1, edit_save_col2 = st.columns([1, 4])
        with edit_save_col1:
            if st.button("💾 Save Changes", type="primary", use_container_width=True):
                st.session_state.edited_document = clean_legal_text(user_edited_text)
                st.session_state.is_editing = False
                st.success("✅ Changes saved! Downloads and preview now reflect your edits.")
                st.rerun()
    else:
        # PREVIEW MODE (Styled Paper Layout)
        with st.container():
            # Build preview HTML
            paper_content = sanitize_html(st.session_state.edited_document)

            # Convert Markdown headers and lists to clean HTML for the paper view
            formatted_html = paper_content.replace("\n", "<br>")

            # Terms Table Preview if applicable
            terms_table_html = ""
            if st.session_state.include_table and len(st.session_state.parsed_terms) > 1:
                rows_html = "".join(
                    f"<tr><td style='text-align:center;'>{i}</td><td>{sanitize_html(t)}</td></tr>"
                    for i, t in enumerate(st.session_state.parsed_terms, 1)
                )
                terms_table_html = f"""
                <div style="margin: 20px 0;">
                    <div style="font-weight: bold; font-size: 14px; margin-bottom: 6px; color: #0F172A; text-transform: uppercase;">
                        Key Terms Summary
                    </div>
                    <table class="preview-terms-table">
                        <thead>
                            <tr>
                                <th style="width: 50px; text-align: center;">No.</th>
                                <th>Agreed Term / Provision</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows_html}
                        </tbody>
                    </table>
                </div>
                """

            preview_card = f"""
            <div class="document-paper">
                {f'<div style="text-align:center; font-weight:bold; letter-spacing:1px; color:#475569; margin-bottom:4px;">{sanitize_html(st.session_state.company_name.upper())}</div>' if st.session_state.company_name else ''}
                <div style="text-align: center; font-size: 22px; font-weight: bold; color: #0F172A; margin-bottom: 8px;">
                    {sanitize_html(st.session_state.doc_title.upper())}
                </div>
                <div style="text-align: center; font-style: italic; color: #64748B; font-size: 14px; margin-bottom: 20px;">
                    Effective Date: {sanitize_html(st.session_state.effective_date)}
                </div>
                <hr>
                {terms_table_html}
                <div style="text-align: justify; margin-top: 15px;">
                    {formatted_html}
                </div>
                {f'<div style="margin-top: 30px; border-top: 1px solid #E2E8F0; padding-top: 10px; font-size: 11px; color: #94A3B8; text-align: right;">{sanitize_html(st.session_state.footer_text)}</div>' if st.session_state.footer_text else ''}
            </div>
            """
            st.markdown(preview_card, unsafe_allow_html=True)

    # --- DOWNLOAD SECTION ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📥 Download Document")
    st.caption("All downloads automatically include your latest edits, company branding, and terms summary table.")

    # Prepare export files from the LATEST edited text
    active_content = st.session_state.edited_document or st.session_state.generated_document
    base_filename = sanitize_filename(st.session_state.doc_title or st.session_state.doc_type, ext="")
    # Strip trailing dot if present
    base_filename = base_filename.rstrip(".")

    # Generate Bytes for each format
    txt_data = generate_txt_bytes(
        content=active_content,
        title=st.session_state.doc_title,
        company_name=st.session_state.company_name,
        footer_text=st.session_state.footer_text,
    )

    docx_data = generate_docx_bytes(
        content=active_content,
        title=st.session_state.doc_title,
        company_name=st.session_state.company_name,
        effective_date=st.session_state.effective_date,
        footer_text=st.session_state.footer_text,
        logo_bytes=st.session_state.logo_bytes,
        terms=";\n".join(st.session_state.parsed_terms),
        include_terms_table=st.session_state.include_table,
    )

    pdf_data = generate_pdf_bytes(
        content=active_content,
        title=st.session_state.doc_title,
        company_name=st.session_state.company_name,
        effective_date=st.session_state.effective_date,
        footer_text=st.session_state.footer_text,
        logo_bytes=st.session_state.logo_bytes,
        terms=";\n".join(st.session_state.parsed_terms),
        include_terms_table=st.session_state.include_table,
    )

    dl_col1, dl_col2, dl_col3 = st.columns(3)

    with dl_col1:
        st.markdown(
            """
            <div class="download-card">
                <h4>📄 Plain Text (.txt)</h4>
                <p style="color: #64748B; font-size: 0.85rem;">Lightweight plain text format for direct text copying.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.download_button(
            label="⬇️ Download TXT",
            data=txt_data,
            file_name=f"{base_filename}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    with dl_col2:
        st.markdown(
            """
            <div class="download-card">
                <h4>📝 Word Document (.docx)</h4>
                <p style="color: #64748B; font-size: 0.85rem;">Formatted Microsoft Word doc with tables and logo.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.download_button(
            label="⬇️ Download DOCX",
            data=docx_data,
            file_name=f"{base_filename}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )

    with dl_col3:
        st.markdown(
            """
            <div class="download-card">
                <h4>📑 Legal PDF (.pdf)</h4>
                <p style="color: #64748B; font-size: 0.85rem;">Print-ready formal PDF with page numbering and headers.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.download_button(
            label="⬇️ Download PDF",
            data=pdf_data,
            file_name=f"{base_filename}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
