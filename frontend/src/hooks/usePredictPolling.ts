import { useCallback, useEffect, useRef, useState } from 'react';
import { api, type BiometrySampleIn } from '../lib/api';

export interface PollState {
  hr: number;
  hrv: number;
  label: number;
  labelName: string;
  confidence: number;
  recommendedAction: string | null;
  isStressMode: boolean;
  lastPredictionId: number | null;
}

const WINDOW_SIZE = 20;
const POLL_MS = 5000;
const SAMPLE_MS = 1000;

export function usePredictPolling(sessionId = 1, userId = 1) {
  const [state, setState] = useState<PollState>({
    hr: 72,
    hrv: 45,
    label: 0,
    labelName: 'calm',
    confidence: 0.91,
    recommendedAction: null,
    isStressMode: false,
    lastPredictionId: null,
  });

  const stressRef = useRef(false);
  const progressRef = useRef(0);
  const windowRef = useRef<BiometrySampleIn[]>([]);

  const runPredict = useCallback(async () => {
    const win = windowRef.current;
    if (win.length < 3) return;
    try {
      const res = await api.predict(sessionId, userId, win);
      setState(prev => ({
        ...prev,
        label: res.label,
        labelName: res.label_name,
        confidence: res.confidence,
        recommendedAction: res.recommended_action,
      }));
    } catch {
      // Backend unavailable — keep last known state
    }
  }, [sessionId, userId]);

  const toggleStressMode = useCallback(() => {
    const next = !stressRef.current;
    stressRef.current = next;
    progressRef.current = 0;
    if (!next) {
      // Reset biometry on stop
      windowRef.current = [];
      setState(prev => ({
        ...prev,
        isStressMode: false,
        label: 0,
        labelName: 'calm',
        confidence: 0.91,
        recommendedAction: null,
        hr: 72,
        hrv: 45,
      }));
    } else {
      setState(prev => ({ ...prev, isStressMode: true }));
      setTimeout(runPredict, 200);
    }
  }, [runPredict]);

  useEffect(() => {
    const sampleTimer = setInterval(() => {
      const stress = stressRef.current;
      const p = progressRef.current;

      if (stress) {
        // 0 → 100 over ~60 s
        progressRef.current = Math.min(100, p + 100 / 60);
      }

      const hr = stress
        ? Math.round(72 + p * 0.28 + (Math.random() - 0.5) * 4)
        : Math.round(72 + (Math.random() - 0.5) * 8);

      const hrv = stress
        ? Math.max(5, 45 * (1 - p * 0.009) + (Math.random() - 0.5) * 3)
        : Math.max(10, 45 + (Math.random() - 0.5) * 12);

      const accel =
        stress && p > 40
          ? parseFloat((0.25 + Math.random() * 0.65).toFixed(3))
          : parseFloat((0.05 + Math.random() * 0.25).toFixed(3));

      const gsr = stress
        ? parseFloat((5 + p * 0.12 + Math.random() * 2).toFixed(2))
        : parseFloat((5 + Math.random() * 3).toFixed(2));

      const sample: BiometrySampleIn = {
        ts: new Date().toISOString(),
        user_id: userId,
        hr: Math.max(50, Math.min(180, hr)),
        hrv_sdnn_ms: parseFloat(hrv.toFixed(1)),
        accel_mag: accel,
        gsr_us: gsr,
      };

      windowRef.current = [...windowRef.current.slice(-(WINDOW_SIZE - 1)), sample];
      setState(prev => ({ ...prev, hr: sample.hr, hrv: sample.hrv_sdnn_ms }));
    }, SAMPLE_MS);

    const pollTimer = setInterval(runPredict, POLL_MS);

    return () => {
      clearInterval(sampleTimer);
      clearInterval(pollTimer);
    };
  }, [runPredict, userId]);

  return { ...state, toggleStressMode };
}
