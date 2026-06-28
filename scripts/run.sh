#!/usr/bin/env bash
set -e

SCRIPTS_DIR="$(dirname "$0")/scripts"
MODEL_DIR="$(dirname "$0")/model"
VIDEOS_DIR="$(dirname "$0")/video"
DATASET="$MODEL_DIR/dataset.csv"
MODEL="$MODEL_DIR/model.pkl"
MODEL_META="$MODEL_DIR/model_meta.json"
INPUT_JSON="${1:-input.json}"
VIDEO_TO_PREDICT="$2"

TMP_META="/tmp/target_meta.json"
TMP_FEAT="/tmp/target_features.json"
TMP_FULL="/tmp/full_input.json"

echo "=== Step 1: extract features from training videos ==="
for video in "$VIDEOS_DIR"/*.mp4; do
    BASE=$(basename "$video" | sed 's/\.[^.]*$//')
    echo "  Processing: $video"
    bash "$SCRIPTS_DIR/extract-metadata.sh" "$video" "$VIDEOS_DIR/${BASE}_meta.json"
    python3 "$SCRIPTS_DIR/extract-features.py" "$video" "$VIDEOS_DIR/${BASE}_features.json"
done

echo "=== Step 2: generate dataset ==="
python3 "$MODEL_DIR/generate-dataset.py" "$DATASET" "$VIDEOS_DIR"/*.mp4

echo "=== Step 3: train model ==="
python3 "$MODEL_DIR/train-model.py" "$DATASET" "$MODEL" "$MODEL_META"

echo "=== Step 4: extract features from target video ==="
bash "$SCRIPTS_DIR/extract-metadata.sh" "$VIDEO_TO_PREDICT" "$TMP_META"
python3 "$SCRIPTS_DIR/extract-features.py" "$VIDEO_TO_PREDICT" "$TMP_FEAT"

echo "=== Step 5: merge into full input ==="
python3 "$SCRIPTS_DIR/merge.py" "$TMP_META" "$TMP_FEAT" "$INPUT_JSON" "$TMP_FULL"

echo "=== Step 6: predict ==="
python3 "$MODEL_DIR/predict.py" "$MODEL" "$MODEL_META" "$TMP_FULL"`