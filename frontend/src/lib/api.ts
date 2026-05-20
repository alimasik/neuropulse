const BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8000';

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`);
  return res.json() as Promise<T>;
}

export interface BiometrySampleIn {
  ts: string;
  user_id: number;
  hr: number;
  hrv_sdnn_ms: number;
  accel_mag: number;
  gsr_us?: number;
}

export interface PredictResponse {
  label: number;
  label_name: string;
  confidence: number;
  recommended_action: string | null;
  features: Record<string, number>;
}

export interface EpisodeOut {
  id: number;
  started_at: string;
  ended_at: string | null;
  severity: number;
  trigger_guess: string | null;
  notes: string | null;
}

export interface PredictionOut {
  id: number;
  ts: string;
  label: number;
  confidence: number;
  recommended: string | null;
}

export interface Stats7d {
  episodes_count: number;
  avg_severity: number;
  top_trigger: string | null;
  critical_events: number;
}

export interface HistoryResponse {
  episodes: EpisodeOut[];
  recent_predictions: PredictionOut[];
  stats_7d: Stats7d;
}

export const api = {
  predict(sessionId: number, userId: number, samples: BiometrySampleIn[]) {
    return req<PredictResponse>('/predict', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId, user_id: userId, samples }),
    });
  },
  feedback(predictionId: number, helpful: boolean, userState: string) {
    return req<{ ok: boolean }>('/feedback', {
      method: 'POST',
      body: JSON.stringify({ prediction_id: predictionId, helpful, user_state: userState }),
    });
  },
  history(userId = 1) {
    return req<HistoryResponse>(`/history?user_id=${userId}`);
  },
};
