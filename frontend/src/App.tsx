import { useEffect, useState } from "react";
import PDFUploader from "./components/PDFUploader";
import TranslationViewer from "./components/TranslationViewer";
import { translatePdf } from "./api";
import { displayTitle } from "./utils";
import type { PipelineReport } from "./types";

const PIPELINE_STEPS = [
  "Parsing PDF...",
  "Translating to Hindi...",
  "Reviewing with Foundry IQ...",
  "Building Report...",
] as const;

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);
  const [report, setReport] = useState<PipelineReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Animate through the pipeline steps while the request is in flight.
  // The backend runs the whole pipeline in one POST, so this is a paced
  // visual estimate that holds on the final step until the response lands.
  useEffect(() => {
    if (!isLoading) return;
    setStepIndex(0);
    const timer = setInterval(() => {
      setStepIndex((i) => Math.min(i + 1, PIPELINE_STEPS.length - 1));
    }, 1400);
    return () => clearInterval(timer);
  }, [isLoading]);

  async function handleTranslate() {
    if (!file) return;
    setError(null);
    setReport(null);
    setIsLoading(true);
    try {
      const result = await translatePdf(file);
      setReport(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="min-h-screen">
      {/* ───────── Header ───────── */}
      <header className="bg-medora-header shadow-lg">
        <div className="mx-auto flex max-w-7xl items-center gap-3 px-6 py-4">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/10 ring-1 ring-white/20">
            <PillIcon />
          </div>
          <div>
            <h1 className="text-xl font-bold leading-tight text-white">
              Medora<span className="text-blue-300">Rx</span>
            </h1>
            <p className="text-xs text-blue-200">
              Medical document translation &amp; terminology review
            </p>
          </div>
          <span className="ml-auto rounded-full bg-white/10 px-3 py-1 text-xs font-medium text-blue-100 ring-1 ring-white/20">
            EN → हिन्दी
          </span>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-8">
        {/* ───────── Upload card ───────── */}
        <section className="mx-auto mb-8 max-w-2xl rounded-2xl bg-white p-6 shadow-md ring-1 ring-slate-200">
          <h2 className="mb-1 text-lg font-semibold text-slate-800">
            Upload a clinical PDF
          </h2>
          <p className="mb-4 text-sm text-slate-500">
            We parse it, translate to Hindi, and verify every medical term against the
            Foundry IQ knowledge base.
          </p>

          <PDFUploader selectedFile={file} onFileSelected={setFile} disabled={isLoading} />

          <button
            onClick={handleTranslate}
            disabled={!file || isLoading}
            className="mt-4 w-full rounded-xl bg-medora-accent px-4 py-3 font-semibold text-white shadow-sm transition-colors hover:bg-medora-header disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            {isLoading ? "Processing…" : "Translate & Review"}
          </button>

          {error && (
            <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              <span className="font-semibold">Error:</span> {error}
            </div>
          )}
        </section>

        {/* ───────── Loading: pipeline progress ───────── */}
        {isLoading && (
          <section className="mx-auto max-w-2xl rounded-2xl bg-white p-6 shadow-md ring-1 ring-slate-200">
            <ol className="space-y-3">
              {PIPELINE_STEPS.map((step, i) => {
                const done = i < stepIndex;
                const active = i === stepIndex;
                return (
                  <li key={step} className="flex items-center gap-3">
                    <span
                      className={[
                        "flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold",
                        done
                          ? "bg-green-500 text-white"
                          : active
                          ? "bg-medora-accent text-white"
                          : "bg-slate-200 text-slate-400",
                      ].join(" ")}
                    >
                      {done ? "✓" : i + 1}
                    </span>
                    <span
                      className={[
                        "text-sm font-medium",
                        done ? "text-slate-400" : active ? "text-slate-800" : "text-slate-400",
                      ].join(" ")}
                    >
                      {step}
                    </span>
                    {active && <Spinner />}
                  </li>
                );
              })}
            </ol>
          </section>
        )}

        {/* ───────── Results ───────── */}
        {report && !isLoading && (
          <section>
            <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
              <h2 className="text-lg font-semibold text-slate-800">
                {displayTitle(report.final_report.document_title)}
              </h2>
              <p className="text-sm text-slate-500">
                {report.final_report.total_sections} sections ·{" "}
                {report.final_report.total_paragraphs} paragraphs ·{" "}
                {report.processed_pages}/{report.total_pages} pages processed
              </p>
            </div>
            <TranslationViewer report={report} />
          </section>
        )}

        {/* ───────── Empty state ───────── */}
        {!report && !isLoading && !error && (
          <div className="py-16 text-center text-slate-400">
            <p className="text-sm">Upload a PDF above to see the 3-panel review.</p>
          </div>
        )}
      </main>
    </div>
  );
}

/* ─────────────────────── icons ─────────────────────── */

function PillIcon() {
  return (
    <svg className="h-5 w-5" viewBox="0 0 32 32" fill="none">
      <rect x="2" y="13" width="28" height="6" rx="3" fill="#ffffff" />
      <rect x="2" y="13" width="14" height="6" rx="3" fill="#93c5fd" />
    </svg>
  );
}

function Spinner() {
  return (
    <svg className="ml-1 h-4 w-4 animate-spin text-medora-accent" viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 0 1 8-8V0C5.4 0 0 5.4 0 12h4z" />
    </svg>
  );
}
