"""MedoraRx FastAPI orchestrator — runs the four-agent translation pipeline."""

import json
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# Make the agents package importable
sys.path.insert(0, str(Path(__file__).parent / "agents"))

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool

from parser_agent     import parse_pdf
from translator_agent import translate_document  as translate
from reviewer_agent   import review_document     as review
from report_builder   import build_report, save_report

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("medorarx")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_OUTPUT_DIR  = Path(__file__).parent.parent / "data" / "output"
_UPLOAD_PATH = _OUTPUT_DIR / "uploaded.pdf"
_REPORT_PATH = _OUTPUT_DIR / "report.json"

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="MedoraRx",
    description="Medical document translation and terminology review pipeline",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok", "service": "MedoraRx", "version": "1.0.0"}


@app.post("/translate")
async def translate_endpoint(file: UploadFile = File(...)):
    """Accept a PDF, run the full pipeline, and return the final report JSON."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    # ── Save upload ──────────────────────────────────────────────────────────
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    content = await file.read()
    _UPLOAD_PATH.write_bytes(content)
    log.info("Uploaded '%s' (%d bytes) → %s", file.filename, len(content), _UPLOAD_PATH)

    # ── Pipeline (each step is CPU/IO-bound; run in thread pool) ─────────────
    try:
        log.info("Step 1/4  Parsing PDF …")
        parsed = await run_in_threadpool(parse_pdf, str(_UPLOAD_PATH))
        log.info(
            "          %d sections, %d paragraphs",
            len(parsed["sections"]),
            sum(len(s["paragraphs"]) for s in parsed["sections"]),
        )

        log.info("Step 2/4  Translating to Hindi …")
        translated = await run_in_threadpool(translate, parsed)
        log.info(
            "          %d paragraphs translated",
            translated["translation_metadata"]["paragraphs_translated"],
        )

        log.info("Step 3/4  Reviewing against Foundry IQ …")
        reviewed = await run_in_threadpool(review, translated)
        rs = reviewed["review_summary"]
        log.info(
            "          %d terms — %d verified, %d ambiguous, %d flagged",
            rs["total_terms_reviewed"], rs["verified"], rs["ambiguous"], rs["flagged"],
        )

        log.info("Step 4/4  Building report …")
        report = await run_in_threadpool(build_report, reviewed)
        await run_in_threadpool(save_report, report)
        fr = report["final_report"]
        log.info(
            "          confidence %d/100 [%s] — %d paragraph(s) need review",
            fr["overall_confidence_score"],
            fr["overall_confidence_label"],
            fr["paragraphs_needing_review"],
        )

    except HTTPException:
        raise
    except Exception as exc:
        log.exception("Pipeline failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Pipeline error: {exc}")

    return report


@app.get("/report")
async def get_report():
    """Return the last saved report, or 404 if none exists yet."""
    if not _REPORT_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="No report found. POST a PDF to /translate first.",
        )
    return json.loads(_REPORT_PATH.read_text(encoding="utf-8"))
