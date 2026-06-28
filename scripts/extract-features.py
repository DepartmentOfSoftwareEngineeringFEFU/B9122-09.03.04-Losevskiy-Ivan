#!/usr/bin/env python3
# извлекает motion/static признаки из видео

import sys
import json
import cv2
import numpy as np


def extract_features(video_path: str) -> dict:
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"Error: cannot open {video_path}", file=sys.stderr)
        sys.exit(1)

    fps        = cap.get(cv2.CAP_PROP_FPS)
    total      = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    step       = max(1, int(fps // 2))

    prev_gray          = None
    frame_diffs        = []
    flow_magnitudes    = []
    spatial_complexity = []
    frame_idx          = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % step != 0:
            frame_idx += 1
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        lap = cv2.Laplacian(gray, cv2.CV_64F)
        spatial_complexity.append(float(lap.var()))

        if prev_gray is not None:
            diff = cv2.absdiff(gray, prev_gray)
            frame_diffs.append(float(diff.mean()))

            flow = cv2.calcOpticalFlowFarneback(
                prev_gray, gray, None,
                0.5, 3, 15, 3, 5, 1.2, 0
            )
            mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            flow_magnitudes.append(float(mag.mean()))

        prev_gray  = gray
        frame_idx += 1

    cap.release()

    diffs = np.array(frame_diffs)
    flows = np.array(flow_magnitudes)

    return {
        "motion_mean":           round(float(flows.mean()), 4),
        "motion_std":            round(float(flows.std()), 4),
        "motion_p95":            round(float(np.percentile(flows, 95)), 4),
        "static_ratio":          round(float((diffs < 2.0).mean()), 4),
        "scene_complexity_mean": round(float(np.mean(spatial_complexity)), 4),
        "scene_cut_rate":        round(float((diffs > diffs.mean() + 2 * diffs.std()).mean()), 4),
        "sampled_frames":        len(flow_magnitudes),
        "total_frames":          total,
        "fps":                   fps,
    }


def main():
    if len(sys.argv) < 3:
        print("Usage: extract-features.py <video> <output.json>", file=sys.stderr)
        sys.exit(1)

    features = extract_features(sys.argv[1])

    with open(sys.argv[2], "w") as f:
        json.dump(features, f, indent=2)

    print(f"Saved to {sys.argv[2]}")


if __name__ == "__main__":
    main()