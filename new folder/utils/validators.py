"""LegalEase - Input Validation Utilities.

Validates user inputs, document parameters, and file uploads.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple


def validate_document_request(
    document_type: Optional[str],
    parties: Optional[str],
    terms: Optional[str],
    effective_date: Any,
) -> Tuple[bool, List[str]]:
    """Validates the core required fields for document generation.

    Returns:
        (is_valid, error_messages)
    """
    errors: List[str] = []

    if not document_type or not document_type.strip():
        errors.append("Document type cannot be empty. Please select or enter a document type.")

    if not parties or not parties.strip():
        errors.append("Parties involved cannot be empty. Please specify the legal parties.")
    elif len(parties.strip()) < 3:
        errors.append("Please provide full descriptive names for the parties involved.")

    if not terms or not terms.strip():
        errors.append("Terms and conditions cannot be empty. Please enter at least one term.")
    elif len(terms.strip()) < 5:
        errors.append("Terms and conditions seem too brief. Please provide meaningful details.")

    if not effective_date:
        errors.append("Effective date is required.")
    else:
        # Check if it's a valid date or date string
        if isinstance(effective_date, (date, datetime)):
            pass
        elif isinstance(effective_date, str):
            if not effective_date.strip():
                errors.append("Effective date cannot be empty.")
            else:
                # Try common date formats
                valid = False
                for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%B %d, %Y", "%d-%m-%Y"):
                    try:
                        datetime.strptime(effective_date.strip(), fmt)
                        valid = True
                        break
                    except ValueError:
                        continue
                if not valid:
                    errors.append(f"Invalid date format: '{effective_date}'. Please use YYYY-MM-DD or standard format.")

    return len(errors) == 0, errors


def validate_logo_file(
    file_bytes: bytes,
    filename: str,
    max_size_mb: int = 5,
) -> Tuple[bool, Optional[str]]:
    """Validates uploaded logo file type and size.

    Allowed extensions: .png, .jpg, .jpeg, .webp
    """
    if not file_bytes:
        return False, "File is empty."

    max_bytes = max_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        return False, f"Logo file size exceeds {max_size_mb}MB limit. Uploaded size: {len(file_bytes) / (1024*1024):.1f}MB."

    allowed_exts = {".png", ".jpg", ".jpeg", ".webp"}
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in allowed_exts:
        return False, f"Unsupported image format '{ext}'. Allowed formats: PNG, JPG, JPEG, WEBP."

    # Validate image header / bytes integrity using Pillow if available
    try:
        from io import BytesIO
        from PIL import Image

        image = Image.open(BytesIO(file_bytes))
        image.verify()
    except Exception as e:
        return False, f"Invalid or corrupted image file: {str(e)}"

    return True, None
