import type { PipelineReport } from "./types";

// Backend base URL. The FastAPI orchestrator runs here with CORS enabled.
const API_BASE = "http://127.0.0.1:8000";

/** Upload a PDF to /translate and return the full pipeline report. */
export async function translatePdf(file: File): Promise<PipelineReport> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/translate`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      /* response had no JSON body */
    }
    throw new Error(detail);
  }

  return res.json();
}
