"""Agent 3 – Medical Reviewer: verify medical terms against Azure AI Search (Foundry IQ)."""

import copy
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

_INDEX_NAME = "medical-terminology-index"

# Flag reasons keyed by KB category — used when a term is ambiguous or missing
_FLAG_REASONS: dict[str, str] = {
    "Drug":        "Drug name — verify transliteration with local pharmacopeia",
    "Drug Class":  "Drug name — verify transliteration with local pharmacopeia",
    "Unit":        "Dosage unit — confirm local standard",
    "Pharmacology":"Pharmacology term — verify with local standard",
}
_DEFAULT_FLAG_REASON = "Clinical term — no verified Hindi equivalent in knowledge base"


# ---------------------------------------------------------------------------
# Search client
# ---------------------------------------------------------------------------

def _make_client() -> SearchClient:
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    key = os.getenv("AZURE_SEARCH_KEY")
    if not endpoint or not key:
        print("ERROR: AZURE_SEARCH_ENDPOINT or AZURE_SEARCH_KEY not set in .env")
        sys.exit(1)
    return SearchClient(
        endpoint=endpoint,
        index_name=_INDEX_NAME,
        credential=AzureKeyCredential(key),
    )


# ---------------------------------------------------------------------------
# Snippet parsing
# Foundry chunked medical_glossary.json into raw text fragments.
# Each snippet is a slice of the JSON array — not a valid JSON document.
# We split by "term_english": occurrences so each section belongs to exactly
# one entry, then regex-extract the fields we need from that section.
# ---------------------------------------------------------------------------

def _parse_snippet_entries(snippet: str) -> list[dict]:
    """Return all glossary entries found in a snippet fragment."""
    entries: list[dict] = []
    # Each section from split starts at a term_english key and runs until the next
    sections = re.split(r'(?="term_english"\s*:)', snippet)
    for section in sections:
        m = re.match(r'"term_english"\s*:\s*"([^"]+)"', section)
        if not m:
            continue
        def _field(key: str) -> str | None:
            fm = re.search(rf'"{key}"\s*:\s*"([^"]+)"', section)
            return fm.group(1) if fm else None
        synonyms_m = re.search(r'"synonyms"\s*:\s*\[([^\]]*)\]', section)
        entries.append({
            "term_english": m.group(1),
            "term_hindi":   _field("term_hindi"),
            "category":     _field("category") or "Unknown",
            "confidence":   _field("confidence") or "low",
            "synonyms":     re.findall(r'"([^"]+)"', synonyms_m.group(1)) if synonyms_m else [],
        })
    return entries


# ---------------------------------------------------------------------------
# Full KB load (one API call, dictionary lookups for all terms)
# ---------------------------------------------------------------------------

def _load_full_kb(client: SearchClient) -> dict[str, dict]:
    """Fetch every chunk from the index and parse all entries into a lookup dict.

    Keyed by lowercase term_english AND lowercase synonyms so any form of a
    term resolves to its canonical entry. One search call replaces per-term
    BM25 queries that struggle with very common words like 'Treatment'.
    """
    kb: dict[str, dict] = {}
    # search_text="*" returns all documents; the glossary is small (~7-10 chunks)
    for doc in client.search(search_text="*", top=100):
        for entry in _parse_snippet_entries(doc.get("snippet", "") or ""):
            term = entry["term_english"].lower()
            kb[term] = entry
            for syn in entry.get("synonyms", []):
                if syn:
                    kb[syn.lower()] = entry
    print(f"         KB loaded: {len(kb)} term/synonym keys from index")
    return kb


# ---------------------------------------------------------------------------
# Build one review result for a single term
# ---------------------------------------------------------------------------

def _make_review(term: str, kb_doc: dict | None, text_hindi: str) -> dict:
    """Produce the review dict for one medical term.

    term_hindi_translated: the KB's verified Hindi form if it appears verbatim
    in the translated paragraph (i.e. the translator used the same form), else None.
    """
    if kb_doc is None:
        return {
            "term_english": term,
            "term_hindi_translated": None,
            "term_hindi_verified": None,
            "category": "Unknown",
            "confidence": "low",
            "status": "flagged",
            "flag_reason": _DEFAULT_FLAG_REASON,
        }

    term_hindi_kb: str | None = kb_doc.get("term_hindi")
    category: str             = kb_doc.get("category", "Unknown")
    confidence: str           = kb_doc.get("confidence", "low")

    # Check whether the translator used the same Hindi form as the KB
    term_hindi_translated = (
        term_hindi_kb
        if (term_hindi_kb and term_hindi_kb in text_hindi)
        else None
    )

    if confidence == "high":
        status = "verified"
        flag_reason = None
    elif confidence == "medium":
        status = "ambiguous"
        flag_reason = _FLAG_REASONS.get(category, _DEFAULT_FLAG_REASON)
    else:
        status = "flagged"
        flag_reason = _FLAG_REASONS.get(category, _DEFAULT_FLAG_REASON)

    return {
        "term_english": term,
        "term_hindi_translated": term_hindi_translated,
        "term_hindi_verified": term_hindi_kb,
        "category": category,
        "confidence": confidence,
        "status": status,
        "flag_reason": flag_reason,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def review_document(translated: dict) -> dict:
    """Add reviewed_terms to each paragraph and a review_summary at the root.

    Args:
        translated: Enriched dict produced by translator_agent.translate_document().

    Returns:
        Deep copy with reviewed_terms on each paragraph and review_summary at root.
    """
    client = _make_client()
    result = copy.deepcopy(translated)

    # Load the entire KB once — avoids BM25 ranking issues for common words
    kb = _load_full_kb(client)

    # Build per-term cache with a simple dict lookup (no more per-term API calls)
    all_terms: set[str] = set(
        term
        for section in result["sections"]
        for para in section["paragraphs"]
        for term in para.get("medical_terms", [])
    )
    kb_cache: dict[str, dict | None] = {
        term: kb.get(term.lower()) for term in all_terms
    }

    # Counters for summary
    total = verified = ambiguous = flagged = 0

    for section in result["sections"]:
        for para in section["paragraphs"]:
            text_hindi: str = para.get("text_hindi", "")
            reviews: list[dict] = []
            for term in para.get("medical_terms", []):
                review = _make_review(term, kb_cache[term], text_hindi)
                reviews.append(review)
                total += 1
                if review["status"] == "verified":
                    verified += 1
                elif review["status"] == "ambiguous":
                    ambiguous += 1
                else:
                    flagged += 1
            para["reviewed_terms"] = reviews

    verified_ratio = verified / total if total > 0 else 0
    if verified_ratio >= 0.8:
        overall_confidence = "high"
    elif verified_ratio >= 0.5:
        overall_confidence = "medium"
    else:
        overall_confidence = "low"

    result["review_summary"] = {
        "total_terms_reviewed": total,
        "verified": verified,
        "ambiguous": ambiguous,
        "flagged": flagged,
        "overall_confidence": overall_confidence,
    }

    return result


# ---------------------------------------------------------------------------
# Main / demo — runs the full pipeline
# ---------------------------------------------------------------------------

def main() -> None:
    sys.path.insert(0, str(Path(__file__).parent))
    from parser_agent import parse_pdf
    from translator_agent import translate_document

    sample_pdf = (
        Path(__file__).parent.parent.parent / "data" / "sample" / "who_malaria_guidelines_2025.pdf"
    )

    print("Step 1 – Parsing …")
    try:
        parsed = parse_pdf(str(sample_pdf))
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    print(f"         {len(parsed['sections'])} sections parsed\n")

    print("Step 2 – Translating to Hindi …")
    translated = translate_document(parsed)
    meta = translated["translation_metadata"]
    print(f"         {meta['paragraphs_translated']} paragraphs translated\n")

    print("Step 3 – Reviewing medical terms against Foundry IQ …")
    reviewed = review_document(translated)
    summary = reviewed["review_summary"]

    print("\n=== Review Summary ===")
    print(f"  Total terms reviewed : {summary['total_terms_reviewed']}")
    print(f"  Verified             : {summary['verified']}")
    print(f"  Ambiguous            : {summary['ambiguous']}")
    print(f"  Flagged              : {summary['flagged']}")
    print(f"  Overall confidence   : {summary['overall_confidence']}")

    # Collect first 5 non-verified terms across all paragraphs
    attention = [
        review
        for section in reviewed["sections"]
        for para in section["paragraphs"]
        for review in para.get("reviewed_terms", [])
        if review["status"] in ("ambiguous", "flagged")
    ][:5]

    if attention:
        print("\n=== First 5 Flagged / Ambiguous Terms ===")
        for r in attention:
            print(
                f"  [{r['status'].upper():9s}] {r['term_english']:<35s} "
                f"verified: {str(r['term_hindi_verified']):<30s} "
                f"reason: {r['flag_reason'] or '—'}"
            )
    else:
        print("\nAll reviewed terms are verified.")


if __name__ == "__main__":
    main()
