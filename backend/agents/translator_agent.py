"""Agent 2 – Translator: add Hindi translations to parser_agent JSON output."""

import copy
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from azure.ai.translation.text import TextTranslationClient
from azure.core.credentials import AzureKeyCredential

_BATCH_SIZE = 10  # Azure Translator accepts up to 100 items; 10 keeps payloads small


# ---------------------------------------------------------------------------
# Client factory
# ---------------------------------------------------------------------------

def _make_client() -> TextTranslationClient:
    key = os.getenv("AZURE_TRANSLATOR_KEY")
    region = os.getenv("AZURE_TRANSLATOR_REGION")
    if not key or not region:
        print("ERROR: AZURE_TRANSLATOR_KEY or AZURE_TRANSLATOR_REGION not set in .env")
        sys.exit(1)
    return TextTranslationClient(
        credential=AzureKeyCredential(key),
        region=region,
    )


# ---------------------------------------------------------------------------
# Batched translation
# ---------------------------------------------------------------------------

def _translate_batch(texts: list[str], client: TextTranslationClient) -> list[str]:
    """Translate a list of strings in one API call. Returns translated strings in the same order."""
    if not texts:
        return []
    results = client.translate(body=texts, to_language=["hi"])
    return [item.translations[0].text for item in results]


def _translate_all(texts: list[str], client: TextTranslationClient) -> list[str]:
    """Translate an arbitrary-length list by splitting into batches of _BATCH_SIZE."""
    translated: list[str] = []
    for start in range(0, len(texts), _BATCH_SIZE):
        batch = texts[start : start + _BATCH_SIZE]
        translated.extend(_translate_batch(batch, client))
    return translated


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def translate_document(parsed: dict) -> dict:
    """Translate every paragraph's 'text' field to Hindi.

    Args:
        parsed: Structured dict produced by parser_agent.parse_pdf().

    Returns:
        Deep copy of parsed with 'text_hindi' added to every paragraph
        and 'translation_metadata' added at the root.
    """
    client = _make_client()
    result = copy.deepcopy(parsed)

    # Collect all paragraphs with their location so we can put results back
    coords: list[tuple[int, int]] = []  # (section_idx, para_idx)
    texts: list[str] = []

    for s_idx, section in enumerate(result["sections"]):
        for p_idx, para in enumerate(section["paragraphs"]):
            coords.append((s_idx, p_idx))
            texts.append(para["text"])

    translated = _translate_all(texts, client)

    for (s_idx, p_idx), hindi_text in zip(coords, translated):
        result["sections"][s_idx]["paragraphs"][p_idx]["text_hindi"] = hindi_text

    result["translation_metadata"] = {
        "source_language": "en",
        "target_language": "hi",
        "paragraphs_translated": len(texts),
        "translation_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
    }

    return result


# ---------------------------------------------------------------------------
# Main / demo
# ---------------------------------------------------------------------------

def main() -> None:
    # Lazy import to avoid circular dependency at module load time
    sys.path.insert(0, str(Path(__file__).parent))
    from parser_agent import parse_pdf

    sample_pdf = (
        Path(__file__).parent.parent.parent / "data" / "sample" / "who_malaria_guidelines_2025.pdf"
    )
    print(f"Step 1 – Parsing: {sample_pdf}")
    try:
        parsed = parse_pdf(str(sample_pdf))
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    total_paragraphs = sum(len(s["paragraphs"]) for s in parsed["sections"])
    print(f"         {len(parsed['sections'])} sections, {total_paragraphs} paragraphs\n")

    print("Step 2 – Translating to Hindi …")
    translated = translate_document(parsed)
    meta = translated["translation_metadata"]
    print(f"         {meta['paragraphs_translated']} paragraphs translated at {meta['translation_timestamp']}\n")

    print("Step 3 – Side-by-side preview (first 2 paragraphs)\n")
    count = 0
    for section in translated["sections"]:
        for para in section["paragraphs"]:
            if count >= 2:
                break
            count += 1
            print(f"[{para['paragraph_id']}] — Section: {section['heading']}")
            print(f"  EN: {para['text'][:200]}")
            print(f"  HI: {para.get('text_hindi', '—')[:200]}")
            print()
        if count >= 2:
            break


if __name__ == "__main__":
    main()
