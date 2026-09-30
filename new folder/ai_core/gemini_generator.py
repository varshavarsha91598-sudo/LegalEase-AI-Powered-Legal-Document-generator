"""LegalEase - Gemini Document Generator.

Integrates with Google Gemini API using configurable models, model fallback,
and robust prompt engineering to produce formal, structured legal agreements.
"""

import os
import time
import warnings
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Filter AFC deprecation/recommendation warning from google.genai
warnings.filterwarnings("ignore", category=UserWarning, module="google.genai")

from utils.sanitizer import clean_legal_text, parse_terms_list

load_dotenv()



class GeminiGenerationError(Exception):
    """Custom exception raised when document generation fails."""
    pass


class GeminiGenerator:
    """Service class for orchestrating legal document generation via Gemini."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model_name = (
            model_name
            or os.getenv("GEMINI_MODEL")
            or "gemini-3.8-flash"
        )
        self._client = None
        self._client_type = None

    def _get_client(self):
        """Initializes and returns the appropriate Gemini client."""
        if not self.api_key or self.api_key.strip() in ("", "your_api_key_here"):
            raise GeminiGenerationError(
                "Gemini API key is not configured. Please set GEMINI_API_KEY in your environment or .env file."
            )

        if self._client is not None:
            return self._client

        # Prefer google.genai (Google GenAI SDK 1.0+)
        try:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
            self._client_type = "genai"
            return self._client
        except Exception:
            pass

        # Fallback to google.generativeai
        try:
            import google.generativeai as genai_legacy
            genai_legacy.configure(api_key=self.api_key)
            self._client = genai_legacy
            self._client_type = "legacy"
            return self._client
        except Exception as e:
            raise GeminiGenerationError(f"Failed to initialize Gemini client: {str(e)}")

    def build_prompt(
        self,
        document_type: str,
        parties: str,
        terms: str,
        effective_date: str,
        company_name: Optional[str] = None,
        preferred_title: Optional[str] = None,
        jurisdiction: Optional[str] = None,
    ) -> str:
        """Constructs an expert legal prompt for Gemini."""
        title = preferred_title.strip() if preferred_title else document_type.upper()
        parsed_terms = parse_terms_list(terms)
        formatted_terms = "\n".join(f"- {t}" for t in parsed_terms) if parsed_terms else terms

        prompt = f"""You are an elite legal drafting expert specializing in formal contracts and commercial agreements.
Your task is to draft a comprehensive, legally structured, and professional "{document_type}".

### DOCUMENT PARAMETERS:
- Document Title: {title}
- Selected Type: {document_type}
- Effective Date: {effective_date}
{f"- Organization / Company: {company_name}" if company_name else ""}
{f"- Governing Jurisdiction: {jurisdiction}" if jurisdiction else "- Governing Jurisdiction: Not specified (use standard legal clause with clear bracketed placeholder [State / Country])"}

### PARTIES INVOLVED:
{parties}

### AGREED TERMS & CONDITIONS (MUST BE PRESERVED AND DETAILED INTO FORMAL CLAUSES):
{formatted_terms}

### DRAFTING & FORMATTING GUIDELINES:
1. OUTPUT FORMAT:
   - Output ONLY the complete legal document.
   - Do NOT include conversational preambles, introductory commentary (e.g. 'Here is your draft:'), or postscript notes.
   - Do NOT wrap output in triple backtick code blocks (like ```markdown).

2. STRUCTURE & SECTIONS:
   - Organize the document into clearly numbered and titled articles or sections (e.g. "SECTION 1. DEFINITIONS", "SECTION 2. SCOPE OF SERVICES", etc.).
   - Adapt the sections logically to the specific document type ({document_type}).
   - Always include standard clauses such as:
     * Preamble & Recitals (identifying parties and date)
     * Core Obligations & Consideration (incorporating all provided terms)
     * Term and Termination
     * Confidentiality & Proprietary Rights (if applicable)
     * Governing Law & Dispute Resolution
     * Severability, Entire Agreement, and Amendments
     * Formal Signature and Execution Block with signature lines for all identified parties.

3. PRESERVATION OF TERMS:
   - Incorporate EVERY user-provided term faithfully. Elaborate on them into clear, enforceable contract language.
   - Do NOT invent fictitious facts, monetary figures, or addresses not supplied by the user. If critical details are missing, use clear bracketed placeholders such as [Notice Address] or [Compensation Amount].

4. TONE & LEGAL PRECISION:
   - Use standard formal legal language (e.g., 'shall', 'covenants', 'warrants').
   - Maintain strict consistency in defined terms, names, and pronouns.

Begin drafting the legal document now:"""
        return prompt

    def generate_document(
        self,
        document_type: str,
        parties: str,
        terms: str,
        effective_date: str,
        company_name: Optional[str] = None,
        preferred_title: Optional[str] = None,
        jurisdiction: Optional[str] = None,
    ) -> str:
        """Generates document content using Gemini API with intelligent fallback models."""
        prompt = self.build_prompt(
            document_type=document_type,
            parties=parties,
            terms=terms,
            effective_date=effective_date,
            company_name=company_name,
            preferred_title=preferred_title,
            jurisdiction=jurisdiction,
        )

        client = self._get_client()

        # Build candidate models list: requested model first, then fallback models
        models_to_try = [self.model_name]
        for fallback in ["gemini-3.7-flash", "gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-flash-latest"]:
            if fallback not in models_to_try:
                models_to_try.append(fallback)

        last_error = None

        for model in models_to_try:
            try:
                if self._client_type == "genai":
                    response = client.models.generate_content(
                        model=model,
                        contents=prompt,
                    )
                    generated_text = response.text
                else:
                    gen_model = client.GenerativeModel(model)
                    response = gen_model.generate_content(prompt)
                    generated_text = response.text

                if generated_text and generated_text.strip():
                    return clean_legal_text(generated_text)
            except Exception as e:
                err_msg = str(e)
                last_error = err_msg
                # If invalid key, don't keep trying other models
                if "API_KEY_INVALID" in err_msg or ("400" in err_msg and "key" in err_msg.lower()):
                    raise GeminiGenerationError(
                        "Invalid Gemini API key. Please check your GEMINI_API_KEY environment variable."
                    )
                # If high demand or not found, try next candidate
                continue

        if last_error:
            if "RESOURCE_EXHAUSTED" in last_error or "429" in last_error:
                raise GeminiGenerationError(
                    "Gemini API quota exceeded or rate limit reached. Please wait a moment and try again."
                )
            raise GeminiGenerationError(f"Failed to generate legal document: {last_error}")

        raise GeminiGenerationError("The AI generator returned an empty response. Please try again.")
