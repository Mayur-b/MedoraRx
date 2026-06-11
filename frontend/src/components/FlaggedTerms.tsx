import type { FlaggedTerm } from "../types";
import { STATUS_STYLES } from "../statusStyles";

interface FlaggedTermsProps {
  terms: FlaggedTerm[];
  // Optional map from term_english -> verified Hindi, so we can show the
  // KB-verified Devanagari form alongside the English term.
  verifiedHindi?: Record<string, string | null>;
}

export default function FlaggedTerms({ terms, verifiedHindi = {} }: FlaggedTermsProps) {
  if (terms.length === 0) {
    return (
      <div className="rounded-lg border border-green-200 bg-green-50 p-4 text-center">
        <p className="text-sm font-medium text-green-700">
          ✓ All terms verified — no flagged or ambiguous terms.
        </p>
      </div>
    );
  }

  return (
    <ul className="space-y-3">
      {terms.map((t) => {
        const style = STATUS_STYLES[t.status];
        const hindi = verifiedHindi[t.term];
        return (
          <li
            key={t.term}
            className={`rounded-lg border ${style.border} ${style.bg} p-3.5 shadow-sm`}
          >
            {/* Header row: warning icon + EN → HI */}
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-baseline gap-2">
                <span className="text-base leading-none">
                  {t.status === "flagged" ? "⚠️" : "❓"}
                </span>
                <span className="font-semibold text-slate-800">{t.term}</span>
                {hindi && (
                  <>
                    <span className="text-slate-400">→</span>
                    <span className="font-hindi text-lg text-slate-800">{hindi}</span>
                  </>
                )}
              </div>
              <span
                className={`shrink-0 rounded-full px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide ${style.badge}`}
              >
                {style.label}
              </span>
            </div>

            {/* Flag reason */}
            {t.flag_reason && (
              <p className={`mt-2 text-sm ${style.text}`}>{t.flag_reason}</p>
            )}

            {/* Appears-in paragraphs */}
            <div className="mt-2 flex flex-wrap items-center gap-1.5">
              <span className="text-xs text-slate-500">Appears in:</span>
              {t.appears_in_paragraphs.map((p) => (
                <span
                  key={p}
                  className="rounded bg-white px-1.5 py-0.5 font-mono text-xs text-slate-600 ring-1 ring-slate-200"
                >
                  {p}
                </span>
              ))}
            </div>
          </li>
        );
      })}
    </ul>
  );
}
