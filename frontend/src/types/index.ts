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

export interface AnalysisResult {
  id?: string;
  project_id: string;
  status: AnalysisStatus;
  summary: AnalysisSummary;
  pitfalls: PitfallItem[];
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

// --- SSE Events ---
export type SSEEventType =
  | 'parsing'
  | 'analyzing'
  | 'progress'
  | 'completed'
  | 'failed';

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