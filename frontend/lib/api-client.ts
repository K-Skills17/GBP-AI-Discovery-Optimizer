import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/* ------------------------------------------------------------------ */
/* Request types                                                       */
/* ------------------------------------------------------------------ */

export interface AuditRequest {
  business_name: string;
  location: string;
  whatsapp?: string;
  delivery_mode?: 'standalone' | 'whatsapp';
}

/* ------------------------------------------------------------------ */
/* Response types                                                      */
/* ------------------------------------------------------------------ */

export interface Competitor {
  rank: number;
  name: string;
  place_id?: string;
  address?: string;
  rating?: number;
  total_reviews: number;
  photos_count: number;
  category?: string;
  website?: string;
  google_maps_url?: string;
  ai_mentioned: boolean;
}

export interface CompetitorAnalysis {
  competitors: Competitor[];
  comparison_matrix: {
    your_business: {
      name: string;
      rating: number;
      total_reviews: number;
      photos_count: number;
      has_website: boolean;
    };
    competitor_average: {
      rating: number;
      total_reviews: number;
      photos_count: number;
    };
    top_competitors: Array<{
      name: string;
      rating: number;
      total_reviews: number;
      photos_count: number;
      has_website: boolean;
    }>;
  };
  gaps: Array<{
    type: string;
    severity: 'high' | 'medium';
    message: string;
    action: string;
  }>;
  ai_mentions: Record<string, boolean>;
  competitive_score: number;
}

export interface Audit {
  id: string;
  business_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  discovery_score?: number;
  competitive_score?: number;
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
  competitor_analysis?: CompetitorAnalysis;
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
  delivery_mode?: string;
  whatsapp_number?: string;
  whatsapp_sent?: boolean;
  whatsapp_sent_at?: string;
  created_at: string;
  updated_at: string;
}

/* ------------------------------------------------------------------ */
/* API calls                                                           */
/* ------------------------------------------------------------------ */

export const createAudit = async (data: AuditRequest): Promise<Audit> => {
  const response = await apiClient.post<Audit>('/audits', data);
  return response.data;
};

export const getAudit = async (auditId: string): Promise<Audit> => {
  const response = await apiClient.get<Audit>(`/audits/${auditId}`);
  return response.data;
};

export const getCompetitors = async (auditId: string): Promise<CompetitorAnalysis> => {
  const response = await apiClient.get<CompetitorAnalysis>(`/audits/${auditId}/competitors`);
  return response.data;
};

export const sendWhatsApp = async (auditId: string): Promise<{ success: boolean; message_id?: string }> => {
  const response = await apiClient.post(`/audits/${auditId}/send-whatsapp`);
  return response.data;
};

export const getReportDownloadUrl = (auditId: string, format: 'pdf' | 'text'): string => {
  const base = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
  return `${base}/audits/${auditId}/report?format=${format}`;
};
