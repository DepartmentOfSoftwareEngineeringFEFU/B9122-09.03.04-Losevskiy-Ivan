#!/usr/bin/env python3
# train_model.py — обучает LightGBM на датасете, сохраняет модель

import sys
import json
import numpy as np
import pandas as pd
import lightgbm as lgb
import joblib
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.preprocessing import StandardScaler


INPUT_COLS = [
    "res_in_w", "res_in_h", "res_out_w", "res_out_h",
    "fps_in", "fps_out",
    "bitrate_in_mbps", "bitrate_out_mbps",   # target bitrate — входной параметр запроса
    "motion_mean", "motion_std", "motion_p95",
    "static_ratio", "scene_complexity_mean", "scene_cut_rate",
]

TARGET_COLS = ["crf", "preset", "aq_mode", "b_frames"]


def load_data(csv_path: str) -> tuple[np.ndarray, np.ndarray]:
    df = pd.read_csv(csv_path)

    # фильтруем строки с плохим VMAF (кодирование упало или качество неприемлемо)
    df = df[df["vmaf"] >= 70].dropna(subset=INPUT_COLS + TARGET_COLS)

    print(f"Dataset size after filtering: {len(df)}")

    X = df[INPUT_COLS].values
    y = df[TARGET_COLS].values
    return X, y


def train(csv_path: str, model_path: str, meta_path: str):
    X, y = load_data(csv_path)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42
    )

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test  = scaler.transform(X_test)

    model = MultiOutputRegressor(
        lgb.LGBMRegressor(
            n_estimators=500,
            learning_rate=0.05,
            num_leaves=63,       # сложность дерева
            min_child_samples=10,# минимум сэмплов в листе, защита от переобучения
            subsample=0.8,       # доля строк на каждое дерево
            colsample_bytree=0.8,# доля признаков на каждое дерево
            random_state=42,
        ),
        n_jobs=-1  # параллельно по всем ядрам
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    print("\nMAE per target:")
    for i, col in enumerate(TARGET_COLS):
        mae = mean_absolute_error(y_test[:, i], y_pred[:, i])
        print(f"  {col}: {mae:.3f}")

    # сохраняем модель и scaler вместе
    joblib.dump({"model": model, "scaler": scaler}, model_path)

    # сохраняем метаданные для инференса
    with open(meta_path, "w") as f:
        json.dump({"input_cols": INPUT_COLS, "target_cols": TARGET_COLS}, f, indent=2)

    print(f"\nModel saved to {model_path}")
    print(f"Meta  saved to {meta_path}")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: train_model.py <dataset.csv> <model.pkl> <meta.json>")
        sys.exit(1)

    train(sys.argv[1], sys.argv[2], sys.argv[3])