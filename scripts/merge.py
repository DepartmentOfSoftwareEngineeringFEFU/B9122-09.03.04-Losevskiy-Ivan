#!/usr/bin/env python3
# собирает metadata.json + features.json + user input.json в один full_input.json

import sys
import json


def merge(meta_path: str, feat_path: str, user_path: str, output_path: str):
    meta = json.load(open(meta_path))
    feat = json.load(open(feat_path))
    user = json.load(open(user_path))

    vstream = next(s for s in meta["streams"] if s["codec_type"] == "video")

    full = {
        "res_in_w":              int(vstream["width"]),
        "res_in_h":              int(vstream["height"]),
        "fps_in":                round(eval(vstream["r_frame_rate"]), 2),
        "bitrate_in_mbps":       round(float(vstream.get("bit_rate", 0)) / 1e6, 3),
        "motion_mean":           feat["motion_mean"],
        "motion_std":            feat["motion_std"],
        "motion_p95":            feat["motion_p95"],
        "static_ratio":          feat["static_ratio"],
        "scene_complexity_mean": feat["scene_complexity_mean"],
        "scene_cut_rate":        feat["scene_cut_rate"],
        "res_out_w":             user["res_out_w"],
        "res_out_h":             user["res_out_h"],
        "fps_out":               user["fps_out"],
        "bitrate_out_mbps":      user["bitrate_out_mbps"],
    }

    with open(output_path, "w") as f:
        json.dump(full, f, indent=2)

    print(f"Saved to {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: merge.py <meta.json> <features.json> <user_input.json> <output.json>", file=sys.stderr)
        sys.exit(1)

    merge(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])