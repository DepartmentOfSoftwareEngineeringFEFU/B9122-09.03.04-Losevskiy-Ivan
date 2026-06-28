#!/usr/bin/env python3
# predict.py — инференс: принимает параметры задания и content features,
#              возвращает параметры кодирования

import sys
import json
import numpy as np
import joblib


PRESET_MAP = {0: "ultrafast", 1: "fast", 2: "medium", 3: "slow", 4: "slower", 5: "veryslow"}


def predict(model_path: str, meta_path: str, input_json: str):
    bundle = joblib.load(model_path)
    model  = bundle["model"]
    scaler = bundle["scaler"]

    with open(meta_path) as f:
        meta = json.load(f)

    with open(input_json) as f:
        data = json.load(f)

    X = np.array([[data[col] for col in meta["input_cols"]]])
    X = scaler.transform(X)

    pred = model.predict(X)[0]

    crf      = int(round(float(pred[0])))
    preset   = int(round(float(pred[1])))
    aq_mode  = int(round(float(pred[2])))
    b_frames = int(round(float(pred[3])))

    # клиппируем в допустимые диапазоны
    crf      = max(18, min(35, crf))
    preset   = max(0,  min(5,  preset))
    aq_mode  = max(0,  min(3,  aq_mode))
    b_frames = max(0,  min(4,  b_frames))

    result = {
        "crf":      crf,
        "preset":   PRESET_MAP[preset],
        "aq_mode":  aq_mode,
        "b_frames": b_frames,
        "ffmpeg_cmd": (
            f"ffmpeg -i input.mp4 -c:v libx265 "
            f"-crf {crf} -preset {PRESET_MAP[preset]} "
            f"-x265-params aq-mode={aq_mode}:bframes={b_frames} "
            f"output.mp4"
        )
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: predict.py <model.pkl> <meta.json> <input.json>")
        sys.exit(1)

    predict(sys.argv[1], sys.argv[2], sys.argv[3])