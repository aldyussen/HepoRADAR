export type Zone = "low" | "grey" | "high";

export interface ScanSummary {
  total: number;
  low: number;
  grey: number;
  high: number;
  lost_count: number;
}

export interface WorklistItem {
  patient_id: number;
  mrn: string;
  age: number | null;
  sex: number | null;          // 0/1, НЕ строка
  fib4: number | null;
  apri: number | null;
  zone: Zone | null;
  ml_risk: number | null;
  is_lost: boolean;
  last_lab_date: string | null; // ISO date "YYYY-MM-DD"
}

export interface WorklistResponse {
  items: WorklistItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface LabEntry {
  analyte: string;
  value: number | null;
  unit: string | null;
  date: string;
  quality_flag: string | null;
}

export interface ScoreEntry {
  lab_date: string;
  fib4: number | null;
  apri: number | null;
  de_ritis: number | null;
  zone: Zone | null;
  ml_risk: number | null;
  is_lost: boolean;
  quality_flags: string | null;
  computed_at: string;         // ISO datetime
}

export interface PatientCard {
  id: number;
  mrn: string;
  age: number | null;
  sex: number | null;
  labs: LabEntry[];            // LONG-формат: одна строка на аналит
  scores: ScoreEntry[];
}

export interface IngestReport {
  rows_processed: number;
  patients_ingested: number;
  labs_ingested: number;
  rows_rejected: number;
  rejected_rows: { row_index: number; reason: string }[];
  quality_flags: Record<string, number>;
}

export interface ReflexFlag {
  type: string;
  msg: string;
}

export interface PatientReflex {
  flags: ReflexFlag[];
}

export const sexLabel = (s: number | null): string => {
  if (s === 1) return "М";
  if (s === 0) return "Ж";
  return "—";
};

export interface ShapFactor {
  feature: string;
  value: string;
  impact: number;
}

export interface CascadeStage {
  stage: string;
  count: number;
  description: string;
}
