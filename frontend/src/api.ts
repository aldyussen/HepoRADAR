import {
  WorklistResponse,
  PatientCard,
  ScanSummary,
  IngestReport,
  Zone,
  ShapFactor,
  CascadeStage,
} from './types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, options);
  
  if (!res.ok) {
    let errMsg = `Ошибка API: ${res.status}`;
    try {
      const text = await res.text();
      try {
        const body = JSON.parse(text);
        if (body && body.detail) {
          errMsg = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
        } else if (body && body.message) {
          errMsg = body.message;
        }
      } catch {
        if (text) errMsg = text;
      }
    } catch {}
    const err = new Error(errMsg);
    (err as any).status = res.status;
    throw err;
  }
  
  return res.json() as Promise<T>;
}

export const api = {
  health: async (): Promise<{ status: string }> => {
    return request<{ status: string }>('/health');
  },

  scanCohort: async (): Promise<ScanSummary> => {
    return request<ScanSummary>('/cohort/scan', { method: 'POST' });
  },

  getWorklist: async (params: {
    zone?: Zone;
    age_min?: number;
    marker?: string;
    page?: number;
    page_size?: number;
  }): Promise<WorklistResponse> => {
    const query = new URLSearchParams();
    if (params.zone) query.append('zone', params.zone);
    if (params.age_min !== undefined && params.age_min !== null) {
      query.append('age_min', String(params.age_min));
    }
    if (params.marker) query.append('marker', params.marker);
    if (params.page !== undefined) query.append('page', String(params.page));
    if (params.page_size !== undefined) query.append('page_size', String(params.page_size));

    const queryString = query.toString();
    return request<WorklistResponse>(`/cohort/worklist${queryString ? `?${queryString}` : ''}`);
  },

  getPatient: async (id: number): Promise<PatientCard> => {
    return request<PatientCard>(`/patients/${id}`);
  },

  ingestCsv: async (file: File): Promise<IngestReport> => {
    const formData = new FormData();
    formData.append('file', file);
    return request<IngestReport>('/ingest', {
      method: 'POST',
      body: formData,
    });
  },

  getPatientExplain: async (id: number): Promise<ShapFactor[]> => {
    return request<ShapFactor[]>(`/patients/${id}/explain`);
  },

  createReferral: async (id: number): Promise<{ text: string }> => {
    return request<{ text: string }>(`/patients/${id}/referral`, { method: 'POST' });
  },

  getHcvCascade: async (): Promise<CascadeStage[]> => {
    return request<CascadeStage[]>('/cascade/hcv');
  },
};
