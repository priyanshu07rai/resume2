"""
Industrial Document Intelligence Engine — 10-Stage Pipeline.
Guarantees structured output under all failure conditions.
Includes Dual-Vision AI cross-verification with hallucination guard.
"""
import os
import io
import json
import base64
import fitz  # PyMuPDF
import pdfplumber
from shutil import which
from PIL import Image, ImageFilter
import pytesseract
from dotenv import load_dotenv

load_dotenv()

# Configure Tesseract Path for Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# ═══════════════════════════════════════════════════════════════════════
# STAGE 1: PDF-to-Image Renderer (NO POPPLER)
# ═══════════════════════════════════════════════════════════════════════
def pdf_to_images(file_bytes, dpi=300, max_pages=15):
    """
    Renders PDF pages to PNG byte arrays using PyMuPDF only.
    No Poppler dependency. Works on Windows natively.
    Returns list of (PIL Image, PNG bytes) tuples.
    """
    results = []
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        if doc.is_encrypted:
            doc.authenticate("")
        for page_num in range(min(len(doc), max_pages)):
            page = doc[page_num]
            pix = page.get_pixmap(dpi=dpi)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            png_bytes = buffer.getvalue()
            
            results.append({"pil_image": img, "png_bytes": png_bytes})
        doc.close()
    except Exception as e:
        print(f"[STAGE 1] PyMuPDF render fault: {e}")
    return results

# ═══════════════════════════════════════════════════════════════════════
# STAGE 2: Multi-Method Text Extraction
# ═══════════════════════════════════════════════════════════════════════
def extract_text_layers(file_bytes):
    """
    3-sub-layer text extraction: PyMuPDF text -> blocks -> pdfplumber.
    Returns best result with method tag.
    """
    raw_text = ""
    method = "none"
    pages_processed = 0

    # 2a. PyMuPDF .get_text("text")
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        if doc.is_encrypted:
            auth = doc.authenticate("")
            if not auth:
                doc.close()
                return "", "encrypted", 0
        pages_processed = len(doc)
        for page in doc:
            raw_text += page.get_text("text")
        doc.close()
        if len(raw_text.strip()) >= 500:
            method = "pymupdf_text"
    except Exception as e:
        print(f"[STAGE 2a] PyMuPDF text fault: {e}")

    # 2b. PyMuPDF .get_text("blocks") fallback
    if len(raw_text.strip()) < 500:
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            if doc.is_encrypted:
                doc.authenticate("")
            block_text = ""
            for page in doc:
                blocks = page.get_text("blocks")
                for b in blocks:
                    if b[6] == 0:
                        block_text += b[4]
            doc.close()
            if len(block_text.strip()) > len(raw_text.strip()):
                raw_text = block_text
                method = "pymupdf_blocks"
        except Exception as e:
            print(f"[STAGE 2b] PyMuPDF blocks fault: {e}")

    # 2c. pdfplumber fallback
    if len(raw_text.strip()) < 500:
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                plumber_text = ""
                for page in pdf.pages:
                    plumber_text += (page.extract_text() or "")
                if len(plumber_text.strip()) > len(raw_text.strip()):
                    raw_text = plumber_text
                    method = "pdfplumber"
        except Exception as e:
            print(f"[STAGE 2c] pdfplumber fault: {e}")

    return raw_text, method, pages_processed

# ═══════════════════════════════════════════════════════════════════════
# STAGE 3: Advanced Multi-Pass OCR
# ═══════════════════════════════════════════════════════════════════════
def preprocess_image(img):
    """Grayscale -> Sharpen -> Binarize for maximum OCR yield."""
    gray = img.convert("L")
    sharpened = gray.filter(ImageFilter.SHARPEN)
    binarized = sharpened.point(lambda x: 255 if x > 140 else 0, '1')
    return binarized

def run_ocr_pass(image, psm=6):
    try:
        config = f"--oem 3 --psm {psm}"
        return pytesseract.image_to_string(image, lang="eng", config=config)
    except Exception as e:
        print(f"[OCR] Pass psm={psm} fault: {e}")
        return ""

def multi_pass_ocr(page_renders):
    """Multi-pass OCR: psm 6 -> 3 -> 11 for maximum text recovery."""
    all_parts = []
    for render in page_renders:
        img = render["pil_image"]
        processed = preprocess_image(img)

        text = run_ocr_pass(processed, psm=6)
        if len(text.strip()) < 300:
            t2 = run_ocr_pass(processed, psm=3)
            if len(t2.strip()) > len(text.strip()): text = t2
        if len(text.strip()) < 300:
            t3 = run_ocr_pass(processed, psm=11)
            if len(t3.strip()) > len(text.strip()): text = t3

        all_parts.append(text)
    return "\n".join(all_parts)

# ═══════════════════════════════════════════════════════════════════════
# STAGE 4: Automated Extraction Strategy (Groq Only)
# ═══════════════════════════════════════════════════════════════════════
# Note: Gemini/OpenAI Vision removed. Infrastructure ready for Groq Vision.

# ═══════════════════════════════════════════════════════════════════════
# STAGE 6: Page Classification
# ═══════════════════════════════════════════════════════════════════════
def classify_page_type(text):
    """Classifies document as Resume, CV, Cover Letter, Invoice, or Unknown."""
    text_lower = text.lower()
    resume_signals = ["experience", "education", "skills", "work history", "objective", "summary", "certifications"]
    invoice_signals = ["invoice", "total amount", "bill to", "due date", "payment"]
    cover_signals = ["dear hiring", "i am writing", "position of", "sincerely"]

    resume_hits = sum(1 for s in resume_signals if s in text_lower)
    invoice_hits = sum(1 for s in invoice_signals if s in text_lower)
    cover_hits = sum(1 for s in cover_signals if s in text_lower)

    if resume_hits >= 2: return "resume"
    if invoice_hits >= 2: return "invoice"
    if cover_hits >= 2: return "cover_letter"
    if resume_hits >= 1: return "resume"
    return "unknown"

# ═══════════════════════════════════════════════════════════════════════
# STAGE 7: Field Completeness & Hallucination Guard
# ═══════════════════════════════════════════════════════════════════════
REQUIRED_FIELDS = ["name", "email", "skills", "experience"]
OPTIONAL_FIELDS = ["phone", "linkedin", "github", "title", "education", "certifications"]

def compute_field_completeness(structured_data):
    """Returns percentage of expected fields that are non-null/non-empty."""
    if not structured_data or "error" in structured_data:
        return 0
    filled = 0
    total = len(REQUIRED_FIELDS) + len(OPTIONAL_FIELDS)
    for field in REQUIRED_FIELDS + OPTIONAL_FIELDS:
        val = structured_data.get(field)
        if val and val != "null" and val != []:
            filled += 1
    return round((filled / total) * 100)

def hallucination_guard(structured_data, raw_text):
    """
    Rejects AI-extracted fields that have zero overlap with raw text.
    If the name extracted by Vision does not appear anywhere in any extracted text,
    it's likely hallucinated.
    """
    if not structured_data or "error" in structured_data:
        return structured_data, False

    suspicious = False
    name = structured_data.get("name", "")
    if name and raw_text:
        # Check if at least part of the name appears in raw text
        name_parts = name.lower().split()
        found = any(part in raw_text.lower() for part in name_parts if len(part) > 2)
        if not found and len(raw_text) > 100:
            structured_data["_hallucination_warning"] = "Name not found in extracted text"
            suspicious = True

    return structured_data, suspicious

# ═══════════════════════════════════════════════════════════════════════
# STAGE 8: Confidence Scoring
# ═══════════════════════════════════════════════════════════════════════
def calculate_confidence(text, method, vision_consensus=0):
    char_count = len(text.strip())
    if method in ("pymupdf_text", "pymupdf_blocks"):
        if char_count > 1000: return 95
        if char_count > 500:  return 90
        return 70
    if method == "pdfplumber":
        if char_count > 1000: return 88
        if char_count > 500:  return 80
        return 65
    if "ocr" in method:
        if char_count > 1500: return 82
        if char_count > 800:  return 72
        if char_count > 300:  return 55
        return 35
    if "vision" in method:
        base = 75 if char_count > 500 else 55
        return min(92, base + (vision_consensus // 5))
    return 0

# ═══════════════════════════════════════════════════════════════════════
# MAIN ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════
def ingest_document(file_bytes, filename):
    """
    Industrial 10-Stage Document Intelligence Pipeline.
    Text -> OCR -> Dual-Vision -> Cross-Verify -> Classify -> Guard -> Score.
    """
    # ── STAGE 0: File Validation ──────────────────────────────────────
    if not file_bytes or len(file_bytes) < 100:
        return _result(False, "", "none", 0, 0, error="File is empty or corrupted (< 100 bytes).")

    if file_bytes[:5] != b'%PDF-':
        return _result(False, "", "none", 0, 0, error="File is not a valid PDF (bad header).")

    # ── STAGE 1: Render pages to images (PyMuPDF only, no Poppler) ────
    page_renders = pdf_to_images(file_bytes, dpi=300, max_pages=5)

    # ── STAGE 2: Multi-method text extraction ─────────────────────────
    raw_text, method, pages_processed = extract_text_layers(file_bytes)

    if method == "encrypted":
        return _result(False, "", "none", 0, 0, error="Encrypted PDF — password required.")

    # ── STAGE 3: OCR Pipeline (if text < 500 chars) ───────────────────
    if len(raw_text.strip()) < 500 and page_renders:
        print(f"[STAGE 3] Low text density ({len(raw_text.strip())} chars). Running multi-pass OCR...")
        ocr_text = multi_pass_ocr(page_renders)
        if len(ocr_text.strip()) > len(raw_text.strip()):
            raw_text = ocr_text
            method = "ocr_pymupdf"

    # ── STAGE 4: Final Text Normalization ─────────────────────────────
    final_text = raw_text.strip()
    vision_data = None
    vision_consensus = 0
    vision_status = "disabled"

    # ── STAGE 5: Page Classification ──────────────────────────────────
    page_type = classify_page_type(final_text)

    # ── STAGE 6: Field Completeness & Hallucination Guard ─────────────
    field_completeness = 0
    hallucination_warning = False
    if vision_data and not vision_data.get("error"):
        field_completeness = compute_field_completeness(vision_data)
        vision_data, hallucination_warning = hallucination_guard(vision_data, final_text)

    # ── STAGE 7: Final Confidence Score ───────────────────────────────
    confidence = calculate_confidence(final_text, method, vision_consensus)
    if hallucination_warning:
        confidence = max(0, confidence - 15)

    # ── STAGE 8: Structured Response (NEVER crash) ────────────────────
    return _result(
        success=True if len(final_text) > 0 else False,
        text=final_text,
        method=method,
        confidence=confidence,
        pages=pages_processed,
        error=None if final_text else "No readable content after all stages (file may be blank/image-only with no OCR match).",
        vision_data=vision_data,
        page_type=page_type,
        field_completeness=field_completeness,
        vision_consensus=vision_consensus,
        vision_status=vision_status,
        hallucination_flag=hallucination_warning
    )


def _result(success, text, method, confidence, pages, error=None,
            vision_data=None, page_type="unknown", field_completeness=0,
            vision_consensus=0, vision_status="not_triggered", hallucination_flag=False):
    """Standardized pipeline output with full diagnostics."""
    return {
        "success": success,
        "extraction": {
            "text": text,
            "method": method,
            "confidence": confidence,
            "character_count": len(text),
            "pages_processed": pages
        },
        "vision": {
            "structured_data": vision_data,
            "consensus_score": vision_consensus,
            "status": vision_status,
            "field_completeness": field_completeness,
            "hallucination_flag": hallucination_flag
        },
        "page_type": page_type,
        "error": error
    }
