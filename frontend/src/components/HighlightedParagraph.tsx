import { Fragment, useRef, useState, type ReactNode } from "react";
import type { ReviewedTerm, TermStatus } from "../types";
import { STATUS_STYLES } from "../statusStyles";

interface HighlightedParagraphProps {
  text: string;
  reviewedTerms: ReviewedTerm[];
  lang: "en" | "hi";
  className?: string;
  id?: string;
  /** Briefly flash a blue border/background (used by click-to-scroll). */
  flash?: boolean;
}

// Inline highlight colours per status.
const HIGHLIGHT: Record<TermStatus, string> = {
  verified: "bg-green-100 text-green-800",
  ambiguous: "bg-orange-100 text-orange-800",
  flagged: "bg-red-100 text-red-800",
};

// Light status colours for use on the dark tooltip background.
const TOOLTIP_STATUS: Record<TermStatus, string> = {
  verified: "text-green-300",
  ambiguous: "text-orange-300",
  flagged: "text-red-300",
};

function escapeRegExp(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/**
 * Build a regex body for a term where internal whitespace/hyphens match any
 * mix of spaces and hyphens. This bridges separator differences between the
 * KB (e.g. "जैव-उपलब्धता") and the translator's output ("जैव उपलब्धता").
 */
function flexiblePattern(s: string): string {
  return s
    .split(/[\s\-‐-―]+/)
    .filter(Boolean)
    .map(escapeRegExp)
    .join("[\\s\\-\\u2010-\\u2015]*");
}

/**
 * Candidate strings to look for in the text for a given term.
 *  - English: just the English term.
 *  - Hindi: verified Hindi, then the translator's Hindi, then the English term
 *    (flagged terms have no verified Hindi, and untranslated drug names often
 *    remain in Latin script inside the Hindi output).
 */
function candidatesFor(rt: ReviewedTerm, lang: "en" | "hi"): (string | null)[] {
  if (lang === "en") return [rt.term_english];
  return [rt.term_hindi_verified, rt.term_hindi_translated, rt.term_english];
}

/**
 * Wrap every reviewed medical term found in `text` with a coloured, hoverable
 * <mark>.
 */
function buildNodes(
  text: string,
  reviewedTerms: ReviewedTerm[],
  lang: "en" | "hi"
): ReactNode[] {
  // Normalise to NFC so Azure's output and the KB strings compare byte-for-byte.
  const normText = text.normalize("NFC");

  // One flexible pattern per unique candidate string, paired with its term.
  const candidates: { term: ReviewedTerm; pattern: string }[] = [];
  const seen = new Set<string>();
  for (const rt of reviewedTerms) {
    for (const cand of candidatesFor(rt, lang)) {
      if (!cand || !cand.trim()) continue;
      const key = cand.normalize("NFC").toLowerCase();
      if (seen.has(key)) continue;
      seen.add(key);
      candidates.push({ term: rt, pattern: flexiblePattern(cand.normalize("NFC")) });
    }
  }
  if (candidates.length === 0) return [normText];

  // Longest patterns first so "severe malaria" wins over "malaria".
  candidates.sort((a, b) => b.pattern.length - a.pattern.length);

  // Word boundaries help for English; Devanagari has no usable \b, so skip it.
  const boundary = lang === "en" ? "\\b" : "";
  const combined = new RegExp(
    `${boundary}(?:${candidates.map((c) => c.pattern).join("|")})${boundary}`,
    "gi"
  );
  // Anchored per-candidate regexes let us map a match back to its owning term.
  const anchored = candidates.map((c) => ({
    term: c.term,
    re: new RegExp(`^(?:${c.pattern})$`, "i"),
  }));

  const nodes: ReactNode[] = [];
  let lastIndex = 0;
  let key = 0;
  let m: RegExpExecArray | null;
  while ((m = combined.exec(normText)) !== null) {
    const matched = m[0];
    if (m.index > lastIndex) {
      nodes.push(<Fragment key={key++}>{normText.slice(lastIndex, m.index)}</Fragment>);
    }
    const owner = anchored.find((a) => a.re.test(matched));
    nodes.push(
      owner ? (
        <TermMark key={key++} term={owner.term}>
          {matched}
        </TermMark>
      ) : (
        <Fragment key={key++}>{matched}</Fragment>
      )
    );
    lastIndex = m.index + matched.length;
    if (m.index === combined.lastIndex) combined.lastIndex++; // guard zero-length
  }
  if (lastIndex < normText.length) {
    nodes.push(<Fragment key={key++}>{normText.slice(lastIndex)}</Fragment>);
  }
  return nodes;
}

export default function HighlightedParagraph({
  text,
  reviewedTerms,
  lang,
  className,
  id,
  flash = false,
}: HighlightedParagraphProps) {
  // border-l stays reserved (transparent) so the flash adds no layout shift.
  const flashClass = flash ? "border-blue-400 bg-blue-50" : "border-transparent";
  return (
    <p
      id={id}
      className={`${className ?? ""} scroll-mt-2 rounded border-l-4 pl-2 transition-colors duration-700 ${flashClass}`}
    >
      {buildNodes(text, reviewedTerms, lang)}
    </p>
  );
}

/* ─────────────────── highlighted term + hover tooltip ─────────────────── */

const TOOLTIP_WIDTH = 176; // px, matches w-44

function TermMark({ term, children }: { term: ReviewedTerm; children: ReactNode }) {
  const status = STATUS_STYLES[term.status];
  const markRef = useRef<HTMLElement>(null);
  // Anchor flips so the tooltip never spills outside the panel.
  const [anchorX, setAnchorX] = useState<"left" | "center" | "right">("center");
  const [anchorY, setAnchorY] = useState<"top" | "bottom">("top");

  function handleEnter() {
    const el = markRef.current;
    if (!el) return;
    // Nearest scrollable panel; fall back to the viewport.
    let container: HTMLElement | null = el.parentElement;
    while (container && !container.classList.contains("panel-scroll")) {
      container = container.parentElement;
    }
    const c = (container ?? document.documentElement).getBoundingClientRect();
    const m = el.getBoundingClientRect();
    const half = TOOLTIP_WIDTH / 2;

    if (m.left - c.left < half) setAnchorX("left");
    else if (c.right - m.right < half) setAnchorX("right");
    else setAnchorX("center");

    // If the term sits near the panel top, drop the tooltip below it instead.
    setAnchorY(m.top - c.top < 96 ? "bottom" : "top");
  }

  const xClass =
    anchorX === "center"
      ? "left-1/2 -translate-x-1/2"
      : anchorX === "left"
      ? "left-0"
      : "right-0";
  const yClass = anchorY === "top" ? "bottom-full mb-1" : "top-full mt-1";

  return (
    <mark
      ref={markRef}
      onMouseEnter={handleEnter}
      className={`group relative cursor-help rounded px-0.5 ${HIGHLIGHT[term.status]}`}
    >
      {children}
      {/* Tooltip — spans (not divs) keep this valid inside a <p>. */}
      <span
        className={`pointer-events-none absolute z-30 hidden w-44 group-hover:block ${xClass} ${yClass}`}
      >
        <span className="block rounded-md bg-slate-800 px-2.5 py-1.5 text-left shadow-lg">
          <span className="block text-[11px] font-semibold text-white">
            {term.term_english}
          </span>
          <span className="mt-0.5 block text-[10px] text-slate-300">
            Category: <span className="text-slate-100">{term.category}</span>
          </span>
          <span className="block text-[10px] text-slate-300">
            Status:{" "}
            <span className={TOOLTIP_STATUS[term.status]}>{status.label}</span>
          </span>
          {term.flag_reason && (
            <span className="mt-0.5 block text-[10px] italic text-slate-400">
              {term.flag_reason}
            </span>
          )}
        </span>
      </span>
    </mark>
  );
}
