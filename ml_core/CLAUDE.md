# ml_core/ — ML-модели и инференс

> Фичи и метки описаны в `docs/data-model.md`. Изменение фичерсета — это **breaking change** контракта; согласовывай с backend.

---

## Стек

- **Python 3.10+**.
- **scikit-learn** — baseline (`RandomForestClassifier` / `GradientBoosting`).
- **XGBoost** — основная модель (если успеем) с tabular-фичами.
- **numpy, pandas** — обработка.
- **joblib** — сериализация модели.

**Запрещено:** TensorFlow, PyTorch, Transformers, HuggingFace. Это табличная классификация на ~10 фичах — нейросетка не нужна.

---

## Структура папки

```text
ml_core/
├── __init__.py
├── feature_extractor.py     # Из окна BiometrySample → dict фичей
├── model_predict.py         # Загрузка модели + inference
├── train.py                 # Скрипт обучения (запускается отдельно)
├── models/
│   └── baseline.joblib      # Сериализованная модель (коммитим в репо)
├── notebooks/
│   └── exploration.ipynb    # EDA на синтетических данных
└── tests/
    └── test_features.py
```

---

## Контракты

### feature_extractor
```text
def extract_features(window: list[BiometrySample], baseline: UserBaseline) -> dict[str, float]
```
Список фичей — строго как в `docs/data-model.md` (раздел "Фичи для ML"). Имена ключей в dict — те же.

### predictor
```text
def predict(features: dict[str, float]) -> tuple[int, float]
    # returns (label, confidence)
```

Загрузка модели — однократная на старт процесса. Не дёргай `joblib.load` в каждом вызове.

---

## Обучение

`train.py` — отдельный скрипт, запускается вручную:

```text
python -m ml_core.train --data ../data/synthetic.csv --out models/baseline.joblib
```

Алгоритм (на MVP):
1. Читаем CSV с уже посчитанными фичами + label.
2. Train/test split 80/20, стратифицировано.
3. Fit RandomForest (max_depth=6, n_estimators=200).
4. Печатаем classification_report, confusion matrix.
5. Сохраняем модель в `models/baseline.joblib`.

Цель по метрикам: **F1-macro ≥ 0.75** на test (на синтетике это реалистично).

---

## Чего НЕ делать

- ❌ Не подключать MLflow/Wandb на MVP.
- ❌ Не делать гиперпараметрический поиск через Optuna — overkill.
- ❌ Не использовать deep learning.
- ❌ Не хранить модель размером > 50 МБ в репо (если внезапно так получилось — что-то не так).
