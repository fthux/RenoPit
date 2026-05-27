// --- Project ---
export interface Project {
  id: string;
  name: string;
  description?: string;
  input_text?: string;
  image_count: number;
  file_count: number;
  status: 'pending' | 'parsing' | 'analyzing' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  description?: string;
}

// --- File ---
export interface ProjectFile {
  id: string;
  project_id: string;
  filename: string;
  original_name: string;
  file_type: 'dxf' | 'dwg' | 'pdf' | 'image' | 'txt' | 'md' | 'docx';
  file_size: number;
  parsed_content?: Record<string, unknown>;
  created_at: string;
}

// --- Image ---
export interface ProjectImage {
  id: string;
  project_id: string;
  filename: string;
  original_name: string;
  file_size: number;
  width?: number;
  height?: number;
  created_at: string;
}

// --- Analysis ---
export type PitfallSeverity = 'critical' | 'high' | 'medium' | 'low';
export type AnalysisStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface PitfallItem {
  id: string;
  category: string;
  description: string;
  severity: PitfallSeverity;
  location?: string;
  suggestion: string;
  critique?: string;
  trap_explanation?: string;
  regulation_ref?: string;
  image_refs?: string[];
  coordinates?: { x: number; y: number }[];
}

export interface AnalysisSummary {
  total_pitfalls: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  score: number; // 0-100
  summary_text?: string;
}

/** 文档分析结果映射表，以 project_file_id 为 key，确保同一文件只保留最新一条分析 */
export type DocumentAnalysesMap = Record<string, DocumentAnalysisResult>;

export interface AnalysisResult {
  id?: string;
  project_id: string;
  status: AnalysisStatus;
  summary: AnalysisSummary;
  pitfalls: PitfallItem[];
  document_analyses?: DocumentAnalysesMap;
  raw_response?: string;
  created_at?: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
}

// --- Report ---
export interface Report {
  id: string;
  project_id: string;
  pdf_path?: string;
  summary: AnalysisSummary;
  pitfalls_count: number;
  generated_at: string;
}

// --- Document Analysis ---
export type DocRiskCategory = 'billing_trap' | 'contract_clause' | 'extra_item';
export type DocumentAnalysisStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface DocumentRiskItem {
  id: string;
  category: DocRiskCategory;
  title: string;
  original_text: string;
  critique?: string;
  financial_consequence?: string;
  suggested_fix?: string;
}

export interface DocumentAnalysisResult {
  id: string;
  project_id: string;
  project_file_id: string;
  status: DocumentAnalysisStatus;
  doc_type: string;
  confidence: number;
  summary: string;
  total_estimated_risk: string;
  risks_count: number;
  risks: DocumentRiskItem[];
  classifications?: Record<string, unknown>;
  error_message?: string;
  completed_at?: string;
  created_at: string;
  extra_item_prediction?: ExtraItemPrediction;
}

export interface DocumentAnalysisList {
  items: DocumentAnalysisResult[];
  total: number;
}

// --- Extra Item Prediction ---
export interface PredictedItem {
  name: string;
  probability: string;
  estimated_amount: number[];
  trigger_phase: string;
  reason: string;
  prevention: string;
}

export interface ExtraItemPrediction {
  quoted_total: number;
  predicted_actual_total: number;
  confidence_range: number[];
  risk_level: string;
  predicted_items: PredictedItem[];
}

// --- Cross Document Checks ---
export interface DiscrepancyItem {
  type: string;
  severity: 'high' | 'medium' | 'low';
  description: string;
  source_a: string;
  source_b: string;
  risk: string;
  suggested_action: string;
}

export interface UnresolvedIssue {
  issue: string;
  first_reported: string;
  last_reported: string;
  status: string;
  severity: string;
  risk: string;
}

export interface ResolvedIssue {
  issue: string;
  first_reported: string;
  resolved_in: string;
  resolution: string;
}

export interface SupervisionTracking {
  total_issues_found: number;
  resolved: number;
  unresolved: number;
  unresolved_items: UnresolvedIssue[];
  resolved_items: ResolvedIssue[];
}

export interface CrossDocumentChecks {
  check_mode: string;
  document_pairs: string[];
  pair_type: string;
  discrepancies: DiscrepancyItem[];
  supervision_tracking?: SupervisionTracking;
}

// --- SSE Events ---
export type SSEEventType =
  | 'parsing'
  | 'analyzing'
  | 'progress'
  | 'completed'
  | 'failed'
  | 'document_analysis_complete';

export interface SSEMessage {
  event: SSEEventType;
  data: {
    progress: number;  // 0-100
    message: string;
    analysis_id?: number;
    result?: AnalysisResult;
    error?: string;
  };
}
