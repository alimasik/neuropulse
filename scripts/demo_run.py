"""
NeuroPulse demo runner for pitch presentation.
Streams synthetic biometry to the local backend per a chosen scenario.

Usage:
    python scripts/demo_run.py --scenario metro_rush --speed 10x
    python scripts/demo_run.py --scenario school_recess --speed 5x
    python scripts/demo_run.py --scenario calm_day --speed 1x --base-url http://localhost:8000
"""
import argparse
import json
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _post(url: str, data: dict) -> dict:
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read())


_LABEL_ICON = {0: "💚 calm", 1: "🟡 rising", 2: "🔴 critical"}
_STATE_RU = {
    "calm":         "Спокойно",
    "rising_slow":  "Нарастание (медленно)",
    "rising_fast":  "Нарастание (быстро)",
    "critical":     "Критично",
    "rising":       "Нарастание",
}


def run(scenario_name: str, speed: int, base_url: str) -> None:
    scenario_path = ROOT / "data" / "scenarios" / f"{scenario_name}.json"
    if not scenario_path.exists():
        print(f"Сценарий не найден: {scenario_path}", file=sys.stderr)
        print(f"Доступные сценарии: {', '.join(p.stem for p in (ROOT / 'data' / 'scenarios').glob('*.json'))}")
        sys.exit(1)

    scenario = json.loads(scenario_path.read_text(encoding="utf-8"))
    total_min = scenario["duration_minutes"]
    real_min = total_min / speed

    print(f"\n{'=' * 52}")
    print(f"  NeuroPulse Demo — {scenario['name']}")
    print(f"  {scenario.get('description', '')}")
    print(f"  {total_min} мин × {speed}x = {real_min:.1f} мин реального времени")
    print(f"  Backend: {base_url}")
    print(f"{'=' * 52}\n")

    from data.generator import generate_window
    import random
    rng = random.Random(42)

    for phase in scenario["phases"]:
        state = phase["state"]
        duration = phase["end_min"] - phase["start_min"]
        phase_label = phase.get("label", _STATE_RU.get(state, state))
        print(f"▶  [{phase['start_min']:02d}–{phase['end_min']:02d} мин]  {phase_label}")

        for minute in range(duration):
            samples = generate_window(state=state, n=30, session_id=1, rng=rng)
            try:
                _post(f"{base_url}/ingest", {"user_id": 1, "session_id": 1, "samples": samples})
                result = _post(f"{base_url}/predict", {"user_id": 1, "session_id": 1, "samples": samples})
                icon = _LABEL_ICON.get(result["label"], "?")
                action = result.get("recommended_action") or "—"
                conf = result.get("confidence", 0)
                print(f"   +{phase['start_min'] + minute:02d}m  {icon}  confidence={conf:.2f}  action={action}")
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", errors="replace")[:500]
                print(f"   ✗ Backend вернул {e.code} {e.reason}. Тело: {body}")
                sys.exit(1)
            except urllib.error.URLError as e:
                print(f"   ✗ Backend недоступен ({e.reason}). Запустите: scripts\\dev.bat")
                sys.exit(1)
            except Exception as e:
                print(f"   ✗ Ошибка: {e}")

            time.sleep(60.0 / speed)

        print()

    print("✓ Сценарий завершён. Откройте http://localhost:5173/doctor для просмотра аналитики.\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="NeuroPulse demo runner")
    parser.add_argument("--scenario", default="metro_rush",
                        help="Имя сценария из data/scenarios/ (без .json)")
    parser.add_argument("--speed", default="10x",
                        help="Ускорение воспроизведения: 10x, 5x, 2x, 1x")
    parser.add_argument("--base-url", default="http://localhost:8000",
                        help="URL backend-а")
    args = parser.parse_args()

    speed_str = args.speed.lower().rstrip("x")
    try:
        speed = int(speed_str)
        if speed < 1:
            raise ValueError
    except ValueError:
        print(f"Неверный формат speed: {args.speed!r}. Пример: 10x", file=sys.stderr)
        sys.exit(1)

    run(scenario_name=args.scenario, speed=speed, base_url=args.base_url)


if __name__ == "__main__":
    main()
