// TypeScript types mirroring the JSON returned by the MedoraRx backend pipeline.

export type TermStatus = "verified" | "ambiguous" | "flagged";
export type ConfidenceLabel = "high" | "medium" | "low";

export interface ReviewedTerm {
  term_english: string;
  term_hindi_translated: string | null;
  term_hindi_verified: string | null;
  category: string;
  confidence: string;
  status: TermStatus;
  flag_reason: string | null;
}

export interface Paragraph {
  paragraph_id: string;
  text: string;
  text_hindi?: string;
  medical_terms: string[];
  reviewed_terms: ReviewedTerm[];
  paragraph_confidence: number;
  needs_review: boolean;
}

export interface Section {
  section_id: string;
  heading: string;
  paragraphs: Paragraph[];
}

export interface FlaggedTerm {
  term: string;
  status: TermStatus;
  flag_reason: string | null;
  appears_in_paragraphs: string[];
}

export interface TermsSummary {
  total: number;
  verified: number;
  ambiguous: number;
  flagged: number;
}

export interface FinalReport {
  document_title: string;
  source_language: string;
  target_language: string;
  total_sections: number;
  total_paragraphs: number;
  paragraphs_needing_review: number;
  overall_confidence_score: number;
  overall_confidence_label: ConfidenceLabel;
  pipeline_timestamp: string;
  terms_summary: TermsSummary;
  flagged_terms: FlaggedTerm[];
}

export interface PipelineReport {
  document_title: string;
  total_pages: number;
  processed_pages: number;
  sections: Section[];
  translation_metadata?: {
    source_language: string;
    target_language: string;
    paragraphs_translated: number;
    translation_timestamp: string;
  };
  review_summary?: {
    total_terms_reviewed: number;
    verified: number;
    ambiguous: number;
    flagged: number;
    overall_confidence: ConfidenceLabel;
  };
  final_report: FinalReport;
}
