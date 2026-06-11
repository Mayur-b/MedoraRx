"""Agent 1 – PDF Parser: extract structured text and tag medical terms."""

import json
import re
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

try:
    import PyPDF2
except ImportError:
    print("ERROR: PyPDF2 not installed. Run: pip install PyPDF2")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------

_GLOSSARY_PATH = Path(__file__).parent.parent.parent / "data" / "medical_glossary.json"
_PAGE_LIMIT_DEFAULT = 10

# Words that look capitalised but are not medical terms
_STOP_WORDS = {
    "The", "This", "That", "These", "Those", "There", "Their", "They",
    "When", "Where", "Which", "While", "What", "With", "Within", "Without",
    "After", "Before", "During", "Under", "Over", "About", "Above", "Below",
    "From", "Into", "Upon", "Between", "Among", "Against", "Through",
    "Also", "Such", "Each", "Both", "Some", "Many", "Most", "More", "Very",
    "High", "Low", "New", "Other", "First", "Second", "Third", "Last",
    "For", "And", "But", "Not", "All", "Any", "How", "Who", "Has", "Have",
    "Table", "Figure", "Box", "Chapter", "Section", "Annex", "Appendix",
    "World", "Health", "Organization", "Global", "National", "International",
    "Countries", "Country", "Population", "People", "Years", "Year",
    "Data", "Study", "Studies", "Report", "Based", "Used", "Using",
    "January", "February", "March", "April", "June", "July", "August",
    "September", "October", "November", "December",
}

# Common drug-name suffixes for pattern-based discovery beyond the glossary
_DRUG_SUFFIX_RE = re.compile(
    r'\b[A-Z][a-z]*(ine|mab|nib|tide|zole|mycin|cillin|cyclin|azole|pril|'
    r'sartan|olol|dipine|statin|lukast|glitazone|gliptin|parin|xaban|'
    r'gatran|prazole|tidine|oxacin|floxacin|vir|navir|fovir|quine)\b'
)

# Section heading patterns
_NUMBERED_SECTION_RE = re.compile(r'^(\d+\.)*\d+\.?\s+[A-Z]')
_CHAPTER_HEADER_RE = re.compile(r'^(CHAPTER|SECTION|ANNEX|APPENDIX|PART)\b', re.IGNORECASE)


# ---------------------------------------------------------------------------
# Glossary
# ---------------------------------------------------------------------------

def _load_glossary() -> dict[str, str]:
    """Return {lowercase_term: canonical_name} including synonyms."""
    if not _GLOSSARY_PATH.exists():
        return {}
    with open(_GLOSSARY_PATH, encoding="utf-8") as f:
        entries = json.load(f)
    lookup: dict[str, str] = {}
    for entry in entries:
        canonical = entry["term_english"]
        lookup[canonical.lower()] = canonical
        for syn in entry.get("synonyms", []):
            if syn:
                lookup[syn.lower()] = canonical
    return lookup


# ---------------------------------------------------------------------------
# Heading detection
# ---------------------------------------------------------------------------

def _is_heading(line: str) -> bool:
    s = line.strip()
    if not s or len(s) < 3 or len(s) > 120:
        return False
    if s.endswith((',', ';')):
        return False
    if _NUMBERED_SECTION_RE.match(s) or _CHAPTER_HEADER_RE.match(s):
        return True
    alpha_words = [w for w in s.split() if w.isalpha()]
    if not alpha_words:
        return False
    cap_ratio = sum(1 for w in alpha_words if w[0].isupper()) / len(alpha_words)
    # Short, mostly title-cased, no trailing full stop
    if len(s) < 80 and cap_ratio >= 0.7 and not s.endswith('.'):
        return True
    # All-caps short line  e.g. "SUMMARY" or "INTRODUCTION"
    if len(s) < 60 and all(w.isupper() for w in alpha_words):
        return True
    return False


# ---------------------------------------------------------------------------
# Medical term extraction
# ---------------------------------------------------------------------------

def _extract_medical_terms(text: str, glossary: dict[str, str]) -> list[str]:
    found: set[str] = set()
    text_lower = text.lower()

    # Glossary + synonym lookup
    for term_lower, canonical in glossary.items():
        if re.search(r'\b' + re.escape(term_lower) + r'\b', text_lower):
            found.add(canonical)

    # Drug-name suffix pattern (catches novel drugs not yet in glossary)
    for m in _DRUG_SUFFIX_RE.finditer(text):
        word = m.group()
        if word not in _STOP_WORDS and len(word) > 4:
            found.add(word)

    return sorted(found)


# ---------------------------------------------------------------------------
# Page text → sections + paragraphs
# ---------------------------------------------------------------------------

def _segment(pages_text: list[str], glossary: dict[str, str]) -> tuple[str, list[dict]]:
    """Return (document_title, sections)."""
    sections: list[dict] = []
    doc_title = ""

    current_heading = "Preamble"
    current_paragraphs: list[dict] = []
    current_lines: list[str] = []
    para_counter = 0
    section_counter = 0

    def flush_paragraph() -> None:
        nonlocal para_counter
        text = " ".join(current_lines).strip()
        current_lines.clear()
        if not text:
            return
        para_counter += 1
        current_paragraphs.append({
            "paragraph_id": f"p{para_counter}",
            "text": text,
            "medical_terms": _extract_medical_terms(text, glossary),
        })

    def flush_section() -> None:
        nonlocal section_counter
        flush_paragraph()
        if current_paragraphs:
            section_counter += 1
            sections.append({
                "section_id": f"s{section_counter}",
                "heading": current_heading,
                "paragraphs": list(current_paragraphs),
            })
            current_paragraphs.clear()

    for page_text in pages_text:
        for line in page_text.splitlines():
            stripped = line.strip()
            if not stripped:
                if current_lines:
                    flush_paragraph()
            elif _is_heading(stripped):
                flush_section()
                current_heading = stripped
                if not doc_title:
                    doc_title = stripped
            else:
                current_lines.append(stripped)

    flush_section()

    if not doc_title and sections:
        doc_title = sections[0]["heading"]

    return doc_title, sections


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_pdf(pdf_path: str, full_document: bool = False) -> dict:
    """Parse a PDF and return structured JSON with sections and medical terms.

    Args:
        pdf_path: Absolute or relative path to the PDF file.
        full_document: If True, process all pages; otherwise limit to 10.

    Returns:
        dict matching the MedoraRx parser output schema.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    glossary = _load_glossary()

    with open(path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        total_pages = len(reader.pages)
        page_limit = total_pages if full_document else min(_PAGE_LIMIT_DEFAULT, total_pages)
        pages_text = [reader.pages[i].extract_text() or "" for i in range(page_limit)]

    doc_title, sections = _segment(pages_text, glossary)

    return {
        "document_title": doc_title,
        "total_pages": total_pages,
        "processed_pages": page_limit,
        "sections": sections,
    }


# ---------------------------------------------------------------------------
# Main / smoke test
# ---------------------------------------------------------------------------

def main() -> None:
    sample_pdf = (
        Path(__file__).parent.parent.parent / "data" / "sample" / "who_malaria_guidelines_2025.pdf"
    )
    print(f"Parsing: {sample_pdf}\n")

    try:
        result = parse_pdf(str(sample_pdf))
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    total_terms = sum(
        len(p["medical_terms"])
        for s in result["sections"]
        for p in s["paragraphs"]
    )
    unique_terms: set[str] = set(
        term
        for s in result["sections"]
        for p in s["paragraphs"]
        for term in p["medical_terms"]
    )

    print(f"Document title : {result['document_title']}")
    print(f"Pages          : {result['processed_pages']} / {result['total_pages']} processed")
    print(f"Sections found : {len(result['sections'])}")
    print(f"Medical terms  : {total_terms} occurrences, {len(unique_terms)} unique")
    print(f"Unique terms   : {sorted(unique_terms)}\n")

    print("--- Section preview (first 3) ---")
    for section in result["sections"][:3]:
        print(f"\n[{section['section_id']}] {section['heading']}")
        for para in section["paragraphs"][:2]:
            preview = para["text"][:150]
            print(f"  {para['paragraph_id']}: {preview}...")
            if para["medical_terms"]:
                print(f"  Terms: {para['medical_terms']}")


if __name__ == "__main__":
    main()
