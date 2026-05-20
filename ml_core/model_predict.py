"""
Rule-based classifier for sensory overload prediction.
No GPU or training required for MVP.
"""
import random
from typing import Dict, Any, Optional


LABEL_NAMES = {
    0: "calm",
    1: "rising",
    2: "critical",
}

RECOMMENDATIONS = {
    0: None,
    1: ["breathing", "quiet_route"],
    2: "aac",
}


def predict(features: Dict[str, float]) -> Dict[str, Any]:
    """
    Predict sensory overload state from extracted features.

    Rule logic:
    - critical (2): hrv_drop_pct > 0.5 AND hr_delta > 20 AND accel_spikes > 5
    - rising (1):   hrv_drop_pct > 0.3 AND hr_delta > 12
    - calm (0):     otherwise

    Returns:
        dict with label, label_name, confidence, recommended_action
    """
    hrv_drop_pct = features.get("hrv_drop_pct", 0.0)
    hr_delta = features.get("hr_delta", 0.0)
    accel_spikes = features.get("accel_spikes", 0.0)
    gsr_slope = features.get("gsr_slope", 0.0)

    noise = random.uniform(-0.05, 0.05)

    # Critical: all three stress indicators elevated
    if hrv_drop_pct > 0.5 and hr_delta > 20 and accel_spikes > 5:
        label = 2
        base_confidence = 0.85
        recommended_action = "aac"

    # Rising: HRV drop + elevated HR, or GSR spiking
    elif (hrv_drop_pct > 0.3 and hr_delta > 12) or gsr_slope > 1.5:
        label = 1
        base_confidence = 0.72
        # Alternate between interventions based on accel level (movement vs static)
        if accel_spikes > 2:
            recommended_action = "quiet_route"
        else:
            recommended_action = "breathing"

    # Calm
    else:
        label = 0
        base_confidence = 0.91
        recommended_action = None

    # Clamp confidence to [0.5, 0.99]
    confidence = max(0.50, min(0.99, base_confidence + noise))

    return {
        "label": label,
        "label_name": LABEL_NAMES[label],
        "confidence": round(confidence, 3),
        "recommended_action": recommended_action,
    }
