"""
Synthetic biometry generator for NeuroPulse.

CLI usage:
    python data/generator.py --scenario metro_rush --out data/sample_session.json
    python data/generator.py --csv --out data/synthetic.csv --windows 10000 --seed 42
"""
import argparse
import json
import math
import random
import csv as csv_mod
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# --- Параметры профилей (биометрика 3 виртуальных пользователей) ----------------

_PROFILES: dict[str, dict[str, float]] = {
    "calm": {
        "hr_base": 72.0, "hr_amp": 3.0, "hr_noise": 2.0,
        "hrv_base": 45.0, "hrv_amp": 5.0, "hrv_noise": 3.0,
        "accel_base": 0.05, "accel_noise": 0.03, "spike_prob": 0.0,
        "gsr_base": 2.0, "gsr_slope": 0.001, "gsr_noise": 0.2,
    },
    "rising_slow": {
        "hr_base": 83.0, "hr_amp": 5.0, "hr_noise": 3.0,
        "hrv_base": 33.0, "hrv_amp": 4.0, "hrv_noise": 3.0,
        "accel_base": 0.10, "accel_noise": 0.06, "spike_prob": 0.04,
        "gsr_base": 4.0, "gsr_slope": 0.015, "gsr_noise": 0.4,
    },
    "rising_fast": {
        "hr_base": 90.0, "hr_amp": 7.0, "hr_noise": 4.0,
        "hrv_base": 26.0, "hrv_amp": 4.0, "hrv_noise": 3.0,
        "accel_base": 0.18, "accel_noise": 0.09, "spike_prob": 0.08,
        "gsr_base": 6.0, "gsr_slope": 0.030, "gsr_noise": 0.7,
    },
    "critical": {
        "hr_base": 100.0, "hr_amp": 10.0, "hr_noise": 6.0,
        "hrv_base": 19.0, "hrv_amp": 3.0, "hrv_noise": 2.0,
        "accel_base": 0.28, "accel_noise": 0.15, "spike_prob": 0.18,
        "gsr_base": 9.0, "gsr_slope": 0.050, "gsr_noise": 1.0,
    },
}

# Псевдонимы для удобства сценариев
_PROFILES["rising"] = _PROFILES["rising_slow"]


# --- Метки по правилам из docs/data-model.md -----------------------------------

_BASELINE_HR = 72.0
_BASELINE_HRV = 45.0


def _label_from_features(
    hr_mean: float, hrv_sdnn: float, accel_spikes: int,
    baseline_hr: float = _BASELINE_HR, baseline_hrv: float = _BASELINE_HRV,
) -> int:
    hr_delta = hr_mean - baseline_hr
    hrv_drop_pct = max(0.0, (baseline_hrv - hrv_sdnn) / baseline_hrv)

    if hrv_drop_pct > 0.50 and hr_delta > 20 and accel_spikes > 5:
        return 2  # critical
    if hrv_drop_pct > 0.30 and hr_delta > 12:
        return 1  # rising
    return 0  # calm


# --- Генерация одного окна (60 сэмплов) ----------------------------------------

def generate_window(
    state: str = "calm",
    n: int = 60,
    session_id: int = 1,
    start_time: datetime | None = None,
    rng: random.Random | None = None,
) -> list[dict[str, Any]]:
    """Одно окно биометрии (60 сэмплов, по одному в секунду)."""
    if start_time is None:
        start_time = datetime.utcnow() - timedelta(seconds=n)
    if rng is None:
        rng = random.Random()

    p = _PROFILES.get(state, _PROFILES["calm"])
    samples = []

    for i in range(n):
        phase = 2 * math.pi * i / n

        hr_val = p["hr_base"] + p["hr_amp"] * math.sin(phase) + rng.gauss(0, p["hr_noise"])
        hr = max(40, min(220, round(hr_val)))

        hrv_val = p["hrv_base"] + p["hrv_amp"] * math.cos(phase * 0.7) + rng.gauss(0, p["hrv_noise"])
        hrv = round(max(5.0, hrv_val), 2)

        if rng.random() < p["spike_prob"]:
            accel = round(rng.uniform(0.55, 1.5), 3)
        else:
            accel = round(abs(rng.gauss(p["accel_base"], p["accel_noise"])), 3)

        gsr_trend = p["gsr_slope"] * i
        gsr = round(max(0.1, p["gsr_base"] + gsr_trend + rng.gauss(0, p["gsr_noise"])), 2)

        samples.append({
            "ts": (start_time + timedelta(seconds=i)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "session_id": session_id,
            "hr": hr,
            "hrv_sdnn_ms": hrv,
            "accel_mag": accel,
            "gsr_us": gsr,
        })

    return samples


# --- Генерация фичей из окна (дублирует ml_core, но без импорта) ----------------

def _extract_features(samples: list[dict], baseline_hr: float, baseline_hrv: float) -> dict[str, float]:
    hrs    = [s["hr"] for s in samples]
    hrvs   = [s["hrv_sdnn_ms"] for s in samples]
    accels = [s["accel_mag"] for s in samples]
    gsrs   = [s["gsr_us"] for s in samples if s.get("gsr_us") is not None]

    hr_mean   = sum(hrs) / len(hrs)
    hr_delta  = hr_mean - baseline_hr
    hrv_sdnn  = sum(hrvs) / len(hrvs)
    hrv_drop  = max(0.0, (baseline_hrv - hrv_sdnn) / baseline_hrv) if baseline_hrv > 0 else 0.0

    n_acc = len(accels)
    accel_var    = sum((a - sum(accels)/n_acc)**2 for a in accels) / max(1, n_acc - 1)
    accel_spikes = sum(1 for a in accels if a > 0.5)

    gsr_mean = sum(gsrs) / len(gsrs) if gsrs else 0.0
    gsr_slope = 0.0
    if len(gsrs) >= 2:
        n = len(gsrs)
        xs = list(range(n))
        xm = sum(xs) / n
        ym = sum(gsrs) / n
        num = sum((x - xm) * (y - ym) for x, y in zip(xs, gsrs))
        den = sum((x - xm) ** 2 for x in xs)
        gsr_slope = num / den if den else 0.0

    return {
        "hr_mean":      round(hr_mean, 2),
        "hr_delta":     round(hr_delta, 2),
        "hrv_sdnn":     round(hrv_sdnn, 2),
        "hrv_drop_pct": round(hrv_drop, 4),
        "accel_var":    round(accel_var, 4),
        "accel_spikes": float(accel_spikes),
        "gsr_mean":     round(gsr_mean, 2),
        "gsr_slope":    round(gsr_slope, 4),
    }


# --- Генерация CSV из сценариев ------------------------------------------------

_STATES_BY_CLASS = {
    0: ["calm"],
    1: ["rising_slow", "rising_fast"],
    2: ["critical"],
}

# Баланс: calm 60%, rising 25%, critical 15%
_CLASS_WEIGHTS = [0.60, 0.25, 0.15]


def generate_dataset(
    n_windows: int = 10000,
    baseline_hr: float = _BASELINE_HR,
    baseline_hrv: float = _BASELINE_HRV,
    seed: int = 42,
) -> list[dict[str, Any]]:
    """Генерирует датасет из n_windows окон с фичами и метками."""
    rng = random.Random(seed)
    rows = []
    start = datetime(2026, 1, 1, 8, 0, 0)

    for i in range(n_windows):
        target_class = rng.choices([0, 1, 2], weights=_CLASS_WEIGHTS)[0]
        state = rng.choice(_STATES_BY_CLASS[target_class])

        window_start = start + timedelta(minutes=i)
        samples = generate_window(state=state, n=60, session_id=i + 1,
                                  start_time=window_start, rng=rng)
        feats = _extract_features(samples, baseline_hr, baseline_hrv)
        label = _label_from_features(
            feats["hr_mean"], feats["hrv_sdnn"], int(feats["accel_spikes"]),
            baseline_hr, baseline_hrv,
        )
        rows.append({**feats, "label": label})

    return rows


# --- Генерация сессии по сценарию JSON -----------------------------------------

def generate_session_from_scenario(scenario_path: str | Path, seed: int = 42) -> list[dict]:
    scenario_path = Path(scenario_path)
    scenario = json.loads(scenario_path.read_text(encoding="utf-8"))

    rng = random.Random(seed)
    all_samples: list[dict] = []
    session_id = 1
    t = datetime.utcnow()

    for phase in scenario["phases"]:
        state   = phase["state"]
        minutes = phase["end_min"] - phase["start_min"]
        n_win   = max(1, minutes)          # одно окно на минуту

        for _ in range(n_win):
            samples = generate_window(state=state, n=60, session_id=session_id,
                                      start_time=t, rng=rng)
            all_samples.extend(samples)
            t += timedelta(seconds=60)
            session_id += 1

    return all_samples


# --- CLI -----------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NeuroPulse synthetic data generator")
    parser.add_argument("--scenario", help="Path to scenario JSON (e.g. data/scenarios/metro_rush.json)")
    parser.add_argument("--out",     required=True, help="Output file path (.json or .csv)")
    parser.add_argument("--csv",     action="store_true", help="Generate feature CSV dataset")
    parser.add_argument("--windows", type=int, default=10000, help="Number of windows for CSV mode")
    parser.add_argument("--seed",    type=int, default=42,    help="Random seed")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    out = Path(args.out)

    if args.csv:
        print(f"Генерирую датасет: {args.windows} окон, seed={args.seed}...")
        rows = generate_dataset(n_windows=args.windows, seed=args.seed)

        # подсчёт баланса
        from collections import Counter
        counts = Counter(r["label"] for r in rows)
        total  = len(rows)
        for lbl, name in [(0, "calm"), (1, "rising"), (2, "critical")]:
            print(f"  label {lbl} ({name}): {counts[lbl]} ({counts[lbl]/total:.1%})")

        out.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = list(rows[0].keys())
        with out.open("w", newline="", encoding="utf-8") as f:
            writer = csv_mod.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"✓ Сохранено в {out}  ({total} строк)")

    elif args.scenario:
        print(f"Генерирую сессию по сценарию: {args.scenario}...")
        samples = generate_session_from_scenario(args.scenario, seed=args.seed)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(samples, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✓ Сохранено в {out}  ({len(samples)} сэмплов)")

    else:
        print("Укажи --csv или --scenario. Смотри --help.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
