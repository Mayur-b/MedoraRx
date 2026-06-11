import { useMemo, useRef, type RefObject } from "react";
import type { PipelineReport } from "../types";
import { confidenceColor, confidenceRing } from "../statusStyles";
import FlaggedTerms from "./FlaggedTerms";
import HighlightedParagraph from "./HighlightedParagraph";

interface TranslationViewerProps {
  report: PipelineReport;
}

export default function TranslationViewer({ report }: TranslationViewerProps) {
  const { sections, final_report: fr } = report;
  const ts = fr.terms_summary;

  // Synced scrolling between the English (Panel 1) and Hindi (Panel 2) panels.
  const enScrollRef = useRef<HTMLDivElement>(null);
  const hiScrollRef = useRef<HTMLDivElement>(null);
  const isSyncing = useRef(false);

  const syncScroll =
    (source: RefObject<HTMLDivElement>, target: RefObject<HTMLDivElement>) => () => {
      if (isSyncing.current) return; // ignore the echo from the programmatic scroll
      const src = source.current;
      const tgt = target.current;
      if (!src || !tgt) return;
      isSyncing.current = true;
      // Match by scroll ratio — the two panels have different content heights
      // (Hindi uses a larger font), so absolute scrollTop would drift apart.
      const maxSrc = src.scrollHeight - src.clientHeight;
      const ratio = maxSrc > 0 ? src.scrollTop / maxSrc : 0;
      tgt.scrollTop = ratio * (tgt.scrollHeight - tgt.clientHeight);
      requestAnimationFrame(() => {
        isSyncing.current = false;
      });
    };

  // Build term_english -> verified Hindi map from every reviewed term in the doc.
  const verifiedHindi = useMemo(() => {
    const map: Record<string, string | null> = {};
    for (const section of sections) {
      for (const para of section.paragraphs) {
        for (const rt of para.reviewed_terms) {
          if (!(rt.term_english in map)) {
            map[rt.term_english] = rt.term_hindi_verified;
          }
        }
      }
    }
    return map;
  }, [sections]);

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
      {/* ───────── Panel 1: English ───────── */}
      <Panel title="Original (English)" accent="bg-slate-700">
        <div
          ref={enScrollRef}
          onScroll={syncScroll(enScrollRef, hiScrollRef)}
          className="panel-scroll max-h-[70vh] space-y-5 overflow-y-auto pr-2"
        >
          {sections.map((section) => (
            <div key={section.section_id}>
              <h3 className="mb-1.5 text-sm font-bold uppercase tracking-wide text-slate-500">
                {section.heading}
              </h3>
              {section.paragraphs.map((para) => (
                <HighlightedParagraph
                  key={para.paragraph_id}
                  text={para.text}
                  reviewedTerms={para.reviewed_terms}
                  lang="en"
                  className="mb-3 text-sm leading-relaxed text-slate-700"
                />
              ))}
            </div>
          ))}
        </div>
      </Panel>

      {/* ───────── Panel 2: Hindi ───────── */}
      <Panel title="Translation (हिन्दी)" accent="bg-medora-accent">
        <div
          ref={hiScrollRef}
          onScroll={syncScroll(hiScrollRef, enScrollRef)}
          className="panel-scroll max-h-[70vh] space-y-5 overflow-y-auto pr-2"
        >
          {sections.map((section) => (
            <div key={section.section_id}>
              <h3 className="mb-1.5 text-sm font-bold uppercase tracking-wide text-slate-500">
                {section.heading}
              </h3>
              {section.paragraphs.map((para) => (
                <HighlightedParagraph
                  key={para.paragraph_id}
                  text={para.text_hindi ?? "—"}
                  reviewedTerms={para.reviewed_terms}
                  lang="hi"
                  className="font-hindi mb-3 text-[1.05rem] text-slate-800"
                />
              ))}
            </div>
          ))}
        </div>
      </Panel>

      {/* ───────── Panel 3: Review ───────── */}
      <Panel title="Foundry IQ Review" accent="bg-medora-header">
        <div className="panel-scroll max-h-[70vh] space-y-5 overflow-y-auto pr-2">
          {/* Confidence score ring */}
          <div className="flex items-center gap-4 rounded-xl bg-slate-50 p-4">
            <ConfidenceRing
              score={fr.overall_confidence_score}
              color={confidenceRing(fr.overall_confidence_score)}
            />
            <div>
              <p className="text-sm text-slate-500">Overall confidence</p>
              <p className={`text-lg font-bold capitalize ${confidenceColor(fr.overall_confidence_label)}`}>
                {fr.overall_confidence_label}
              </p>
              <p className="text-xs text-slate-400">
                {fr.paragraphs_needing_review} of {fr.total_paragraphs} paragraphs need review
              </p>
            </div>
          </div>

          {/* Terms summary */}
          <div>
            <p className="mb-2 text-sm font-semibold text-slate-600">
              Terms reviewed: {ts.total}
            </p>
            <div className="grid grid-cols-3 gap-2">
              <StatCard label="Verified" value={ts.verified} className="bg-green-50 text-green-700" />
              <StatCard label="Ambiguous" value={ts.ambiguous} className="bg-orange-50 text-orange-700" />
              <StatCard label="Flagged" value={ts.flagged} className="bg-red-50 text-red-700" />
            </div>
          </div>

          {/* Flagged / ambiguous terms reasoning trace */}
          <div>
            <p className="mb-2 text-sm font-semibold text-slate-600">
              Reasoning trace
            </p>
            <FlaggedTerms terms={fr.flagged_terms} verifiedHindi={verifiedHindi} />
          </div>
        </div>
      </Panel>
    </div>
  );
}

/* ─────────────────────── small presentational helpers ─────────────────────── */

function Panel({
  title,
  accent,
  children,
}: {
  title: string;
  accent: string;
  children: React.ReactNode;
}) {
  return (
    <div className="overflow-hidden rounded-2xl bg-white shadow-md ring-1 ring-slate-200">
      <div className={`${accent} px-4 py-2.5`}>
        <h2 className="text-sm font-semibold text-white">{title}</h2>
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}

function StatCard({
  label,
  value,
  className,
}: {
  label: string;
  value: number;
  className: string;
}) {
  return (
    <div className={`rounded-lg p-2.5 text-center ${className}`}>
      <p className="text-xl font-bold">{value}</p>
      <p className="text-[11px] font-medium uppercase tracking-wide">{label}</p>
    </div>
  );
}

function ConfidenceRing({ score, color }: { score: number; color: string }) {
  const radius = 28;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  return (
    <div className="relative h-20 w-20 shrink-0">
      <svg className="h-20 w-20 -rotate-90" viewBox="0 0 70 70">
        <circle cx="35" cy="35" r={radius} fill="none" stroke="#e2e8f0" strokeWidth="6" />
        <circle
          cx="35"
          cy="35"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 1s ease-out" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-lg font-bold text-slate-800">{score}</span>
        <span className="text-[10px] text-slate-400">/ 100</span>
      </div>
    </div>
  );
}
