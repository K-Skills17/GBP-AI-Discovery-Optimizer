import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface AuditRequest {
  business_name: string;
  location: string;
}

export interface Audit {
  id: string;
  business_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  discovery_score?: number;
  sentiment_score?: number;
  visual_coverage_score?: number;
  ai_summary?: {
    ai_summary: string;
    target_audience: string;
    key_attributes: string[];
    missing_signals: string[];
    confidence_score: number;
  };
  sentiment_analysis?: {
    topics: Record<string, number>;
    gaps: Array<{
      claimed: string;
      evidence_score: number;
      status: string;
      recommendation?: string;
    }>;
    positive_signals: string[];
    negative_signals: string[];
  };
  conversational_queries?: Array<{
    query: string;
    query_type: string;
    relevance_score: number;
  }>;
  visual_audit?: {
    photo_count: number;
    coverage_score: number;
    recommendations: string[];
  };
  recommendations?: Array<{
    action: string;
    priority: string;
    impact: string;
    effort: string;
    category: string;
    template?: string;
    detail?: string;
  }>;
  processing_time_seconds?: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export const createAudit = async (data: AuditRequest): Promise<Audit> => {
  const response = await apiClient.post<Audit>('/audits', data);
  return response.data;
};

export const getAudit = async (auditId: string): Promise<Audit> => {
  const response = await apiClient.get<Audit>(`/audits/${auditId}`);
  return response.data;
};

/** Base URL for report download (no axios, to allow browser download with auth/cookies if needed) */
export const getReportDownloadUrl = (auditId: string, format: 'pdf' | 'text'): string => {
  const base = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
  return `${base}/audits/${auditId}/report?format=${format}`;
};
