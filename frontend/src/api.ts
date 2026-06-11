import type { PipelineReport } from "./types";

// Backend base URL. The FastAPI orchestrator runs here with CORS enabled.
const API_BASE = "http://127.0.0.1:8000";

// The full pipeline (parse → translate → review → report) can take a while,
// so allow up to two minutes before giving up.
const TIMEOUT_MS = 120_000;

/** Upload a PDF to /translate and return the full pipeline report. */
export async function translatePdf(file: File): Promise<PipelineReport> {
  const formData = new FormData();
  formData.append("file", file);

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS);

  let res: Response;
  try {
    res = await fetch(`${API_BASE}/translate`, {
      method: "POST",
      body: formData,
      signal: controller.signal,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error(
        "Translation timed out after 120 seconds. Please try again."
      );
    }
    throw new Error(
      "Could not reach the server. Is the backend running on http://127.0.0.1:8000?"
    );
  } finally {
    clearTimeout(timeout);
  }

  if (!res.ok) {
    // Prefer the backend's detail message; otherwise a generic retry prompt.
    let detail = "Please try again.";
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      /* response had no JSON body */
    }
    throw new Error(`Translation failed (${res.status}). ${detail}`);
  }

  return res.json();
}
