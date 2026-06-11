import type { TermStatus, ConfidenceLabel } from "./types";

// Centralised colour coding so every component agrees on green/orange/red.
interface StatusStyle {
  text: string;
  bg: string;
  border: string;
  badge: string;
  label: string;
}

export const STATUS_STYLES: Record<TermStatus, StatusStyle> = {
  verified: {
    text: "text-green-700",
    bg: "bg-green-50",
    border: "border-green-200",
    badge: "bg-green-100 text-green-800",
    label: "Verified",
  },
  ambiguous: {
    text: "text-orange-700",
    bg: "bg-orange-50",
    border: "border-orange-200",
    badge: "bg-orange-100 text-orange-800",
    label: "Ambiguous",
  },
  flagged: {
    text: "text-red-700",
    bg: "bg-red-50",
    border: "border-red-200",
    badge: "bg-red-100 text-red-800",
    label: "Flagged",
  },
};

export function confidenceColor(label: ConfidenceLabel): string {
  if (label === "high") return "text-green-600";
  if (label === "medium") return "text-orange-500";
  return "text-red-600";
}

export function confidenceRing(score: number): string {
  if (score >= 80) return "#16a34a";
  if (score >= 50) return "#ea580c";
  return "#dc2626";
}
