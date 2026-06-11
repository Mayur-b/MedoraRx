"""Agent 4 – Report Builder: assemble the final MedoraRx review report."""

import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

_OUTPUT_PATH = Path(__file__).parent.parent.parent / "data" / "output" / "report.json"

# Confidence thresholds
_REVIEW_THRESHOLD = 80      # paragraphs scoring below this need human review
_LABEL_HIGH       = 80
_LABEL_MEDIUM     = 50


# ---------------------------------------------------------------------------
# Paragraph-level scoring
# ---------------------------------------------------------------------------

def _paragraph_confidence(para: dict) -> int:
    """Return a 0-100 confidence score for one paragraph.

    Formula:
        base  = (verified_count / total_count) * 100
        score = base - (ambiguous_count * 5) - (flagged_count * 15)

    Paragraphs with no reviewed terms are scored 100 (nothing to verify).
    Result is clamped to [0, 100] and rounded to the nearest integer.
    """
    reviewed = para.get("reviewed_terms", [])
    if not reviewed:
        return 100

    total     = len(reviewed)
    verified  = sum(1 for r in reviewed if r["status"] == "verified")
    ambiguous = sum(1 for r in reviewed if r["status"] == "ambiguous")
    flagged_c = sum(1 for r in reviewed if r["status"] == "flagged")

    base  = (verified / total) * 100
    score = base - (ambiguous * 5) - (flagged_c * 15)
    return max(0, min(100, round(score)))


# ---------------------------------------------------------------------------
# Document-level aggregation
# ---------------------------------------------------------------------------

def _collect_flagged_terms(sections: list[dict]) -> list[dict]:
    """Return one entry per unique non-verified term, listing every paragraph it appears in."""
    term_map: dict[str, dict] = {}
    for section in sections:
        for para in section["paragraphs"]:
            para_id = para["paragraph_id"]
            for review in para.get("reviewed_terms", []):
                if review["status"] == "verified":
                    continue
                term = review["term_english"]
                if term not in term_map:
                    term_map[term] = {
                        "term":                   term,
                        "status":                 review["status"],
                        "flag_reason":            review["flag_reason"],
                        "appears_in_paragraphs":  [],
                    }
                if para_id not in term_map[term]["appears_in_paragraphs"]:
                    term_map[term]["appears_in_paragraphs"].append(para_id)
    return list(term_map.values())


def _confidence_label(score: int) -> str:
    if score >= _LABEL_HIGH:
        return "high"
    if score >= _LABEL_MEDIUM:
        return "medium"
    return "low"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_report(reviewed: dict) -> dict:
    """Attach per-paragraph scores and a final_report to the reviewed pipeline output.

    Args:
        reviewed: Dict produced by reviewer_agent.review_document().

    Returns:
        Deep copy with paragraph_confidence + needs_review on every paragraph
        and a final_report object at the root.
    """
    result = copy.deepcopy(reviewed)

    # --- Pass 1: score every paragraph ---
    total_paragraphs         = 0
    paragraphs_needing_review = 0
    scores: list[int]        = []

    for section in result["sections"]:
        for para in section["paragraphs"]:
            score = _paragraph_confidence(para)
            para["paragraph_confidence"] = score
            para["needs_review"]         = score < _REVIEW_THRESHOLD
            total_paragraphs += 1
            scores.append(score)
            if para["needs_review"]:
                paragraphs_needing_review += 1

    # --- Pass 2: document-level aggregates ---
    overall_score = round(sum(scores) / len(scores)) if scores else 100
    flagged_terms = _collect_flagged_terms(result["sections"])
    review_summary = reviewed.get("review_summary", {})
    meta           = reviewed.get("translation_metadata", {})

    result["final_report"] = {
        "document_title":              reviewed.get("document_title", ""),
        "source_language":             meta.get("source_language", "en"),
        "target_language":             meta.get("target_language", "hi"),
        "total_sections":              len(result["sections"]),
        "total_paragraphs":            total_paragraphs,
        "paragraphs_needing_review":   paragraphs_needing_review,
        "overall_confidence_score":    overall_score,
        "overall_confidence_label":    _confidence_label(overall_score),
        "pipeline_timestamp":          datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        "terms_summary": {
            "total":     review_summary.get("total_terms_reviewed", 0),
            "verified":  review_summary.get("verified",  0),
            "ambiguous": review_summary.get("ambiguous", 0),
            "flagged":   review_summary.get("flagged",   0),
        },
        "flagged_terms": flagged_terms,
    }

    return result


def save_report(report: dict) -> Path:
    """Write the report JSON to data/output/report.json and return the path."""
    _OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return _OUTPUT_PATH


# ---------------------------------------------------------------------------
# Main / demo — runs the full four-agent pipeline
# ---------------------------------------------------------------------------

def main() -> None:
    sys.path.insert(0, str(Path(__file__).parent))
    from parser_agent     import parse_pdf
    from translator_agent import translate_document
    from reviewer_agent   import review_document

    sample_pdf = (
        Path(__file__).parent.parent.parent / "data" / "sample" / "who_malaria_guidelines_2025.pdf"
    )

    print("Step 1 – Parsing …")
    try:
        parsed = parse_pdf(str(sample_pdf))
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    print(f"         {len(parsed['sections'])} sections, "
          f"{sum(len(s['paragraphs']) for s in parsed['sections'])} paragraphs\n")

    print("Step 2 – Translating to Hindi …")
    translated = translate_document(parsed)
    print(f"         {translated['translation_metadata']['paragraphs_translated']} paragraphs translated\n")

    print("Step 3 – Reviewing against Foundry IQ …")
    reviewed = review_document(translated)
    rs = reviewed["review_summary"]
    print(f"         {rs['total_terms_reviewed']} terms — "
          f"{rs['verified']} verified, {rs['ambiguous']} ambiguous, {rs['flagged']} flagged\n")

    print("Step 4 – Building report …")
    report = build_report(reviewed)
    fr     = report["final_report"]

    # 1. Final report summary
    print("\n" + "=" * 55)
    print("  FINAL REPORT SUMMARY")
    print("=" * 55)
    print(f"  Document   : {fr['document_title']}")
    print(f"  Languages  : {fr['source_language'].upper()} → {fr['target_language'].upper()}")
    print(f"  Sections   : {fr['total_sections']}")
    print(f"  Paragraphs : {fr['total_paragraphs']}  "
          f"({fr['paragraphs_needing_review']} need review)")
    print(f"  Confidence : {fr['overall_confidence_score']}/100  "
          f"[{fr['overall_confidence_label'].upper()}]")
    ts_str = fr["terms_summary"]
    print(f"  Terms      : {ts_str['total']} total — "
          f"{ts_str['verified']} verified / "
          f"{ts_str['ambiguous']} ambiguous / "
          f"{ts_str['flagged']} flagged")
    print(f"  Timestamp  : {fr['pipeline_timestamp']}")

    # 2. Paragraphs needing review
    needs_review = [
        (section["heading"], para)
        for section in report["sections"]
        for para in section["paragraphs"]
        if para.get("needs_review")
    ]
    if needs_review:
        print(f"\n{'─' * 55}")
        print("  PARAGRAPHS NEEDING REVIEW")
        print(f"{'─' * 55}")
        for heading, para in needs_review:
            preview = para["text"][:100].replace("\n", " ")
            print(f"  [{para['paragraph_id']}] score={para['paragraph_confidence']:3d}  "
                  f"section='{heading}'")
            print(f"       {preview}…")
    else:
        print("\n  All paragraphs passed confidence threshold.")

    # 3. Flagged / ambiguous terms
    if fr["flagged_terms"]:
        print(f"\n{'─' * 55}")
        print("  FLAGGED / AMBIGUOUS TERMS")
        print(f"{'─' * 55}")
        for ft in fr["flagged_terms"]:
            paras = ", ".join(ft["appears_in_paragraphs"])
            print(f"  [{ft['status'].upper():9s}] {ft['term']:<35s} paragraphs: {paras}")
            if ft["flag_reason"]:
                print(f"             → {ft['flag_reason']}")
    else:
        print("\n  No flagged or ambiguous terms.")

    # Save
    saved_path = save_report(report)
    print(f"\n  Report saved → {saved_path}\n")


if __name__ == "__main__":
    main()
