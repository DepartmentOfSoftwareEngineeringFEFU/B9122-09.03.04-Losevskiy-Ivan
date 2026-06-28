#!/usr/bin/env python3
# generate_dataset.py — генерирует датасет запуская ffmpeg с разными параметрами

import subprocess
import json
import os
import csv
import itertools
import tempfile
from pathlib import Path


VMAF_MODEL = "/usr/share/model/vmaf_v0.6.1.json"  # путь к модели VMAF
FFMPEG = "/usr/bin/ffmpeg"
FFPROBE = "/usr/bin/ffprobe"


def run_ffmpeg(input_path: str, output_path: str, params: dict) -> bool:
    preset_map = {0: "ultrafast", 1: "fast", 2: "medium", 3: "slow", 4: "slower", 5: "veryslow"}

    cmd = [
        FFMPEG, "-y",           # -y: перезаписывать без подтверждения
        "-i", input_path,
        "-c:v", "libx265",
        "-crf",     str(params["crf"]),
        "-preset",  preset_map[params["preset"]],
        "-x265-params",
        f"aq-mode={params['aq_mode']}:bframes={params['b_frames']}",
        "-an",                    # -an: без аудио (ускоряет тест)
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0


def get_vmaf(reference: str, distorted: str) -> float | None:
    cmd = [
        FFMPEG,
        "-i", distorted,
        "-i", reference,
        "-lavfi", f"libvmaf=model=path={VMAF_MODEL}:log_fmt=json:log_path=/tmp/vmaf.json",
        "-f", "null", "-"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=300)  # 5 минут максимум
    except subprocess.TimeoutExpired:
        print("  VMAF timeout", file=sys.stderr)
        return None

    if result.returncode != 0:
        print(result.stderr.decode()[-1000:], file=sys.stderr)
        return None

    try:
        with open("/tmp/vmaf.json") as f:
            data = json.load(f)
        return data["pooled_metrics"]["vmaf"]["mean"]
    except Exception as e:
        print(f"  VMAF parse error: {e}", file=sys.stderr)
        return None


def get_filesize_mb(path: str) -> float:
    return os.path.getsize(path) / (1024 * 1024)


def generate_dataset(videos: list[str], output_csv: str):
    # сетка параметров для перебора
    param_grid = {
        "crf":      [18, 22, 26, 30, 35],
        "preset":   [0, 1, 2, 3, 4, 5],
        "aq_mode":  [0, 1, 2, 3],
        "b_frames": [0, 2, 4],
    }

    combinations = list(itertools.product(*param_grid.values()))
    keys = list(param_grid.keys())

    fieldnames = [
        # input features
        "res_in_w", "res_in_h", "res_out_w", "res_out_h",
        "fps_in", "fps_out",
        "bitrate_in_mbps",
        "motion_mean", "motion_std", "motion_p95",
        "static_ratio", "scene_complexity_mean", "scene_cut_rate",
        # encoding params (target)
        "crf", "preset", "aq_mode", "b_frames",
        # качество результата
        "vmaf", "filesize_mb", "bitrate_out_mbps",
    ]

    with open(output_csv, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for video_path in videos:
            print(f"\nProcessing: {video_path}")

            # загружаем content features
            feat_path = video_path.replace(".mp4", "_features.json")
            if not os.path.exists(feat_path):
                print(f"  No features file: {feat_path}, skip")
                continue

            with open(feat_path) as f:
                feat = json.load(f)

            # метаданные через ffprobe
            probe = subprocess.run(
                [FFPROBE, "-v", "quiet", "-print_format", "json",
                 "-show_streams", video_path],
                capture_output=True, text=True
            )
            meta = json.loads(probe.stdout)
            vstream = next(s for s in meta["streams"] if s["codec_type"] == "video")

            res_w       = int(vstream["width"])
            res_h       = int(vstream["height"])
            fps_in      = eval(vstream["r_frame_rate"])  # "30/1" → 30.0
            bitrate_in  = float(vstream.get("bit_rate", 0)) / 1e6

            for combo in combinations:
                params = dict(zip(keys, combo))

                with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                    out_path = tmp.name

                try:
                    ok = run_ffmpeg(video_path, out_path, params)
                    if not ok:
                        continue

                    vmaf        = get_vmaf(video_path, out_path)
                    filesize_mb = get_filesize_mb(out_path)

                    # битрейт выходного файла
                    probe_out = subprocess.run(
                        [FFPROBE, "-v", "quiet", "-print_format", "json",
                         "-show_streams", out_path],
                        capture_output=True, text=True
                    )
                    meta_out    = json.loads(probe_out.stdout)
                    vstream_out = next(s for s in meta_out["streams"] if s["codec_type"] == "video")
                    bitrate_out = float(vstream_out.get("bit_rate", 0)) / 1e6

                    row = {
                        "res_in_w":             res_w,
                        "res_in_h":             res_h,
                        "res_out_w":            res_w,   # если добавишь ресайз — менять здесь
                        "res_out_h":            res_h,
                        "fps_in":               round(fps_in, 2),
                        "fps_out":              round(fps_in, 2),
                        "bitrate_in_mbps":      round(bitrate_in, 3),
                        "motion_mean":          feat["motion_mean"],
                        "motion_std":           feat["motion_std"],
                        "motion_p95":           feat["motion_p95"],
                        "static_ratio":         feat["static_ratio"],
                        "scene_complexity_mean":feat["scene_complexity_mean"],
                        "scene_cut_rate":       feat["scene_cut_rate"],
                        "crf":                  params["crf"],
                        "preset":               params["preset"],
                        "aq_mode":              params["aq_mode"],
                        "b_frames":             params["b_frames"],
                        "vmaf":                 round(vmaf, 4) if vmaf else None,
                        "filesize_mb":          round(filesize_mb, 3),
                        "bitrate_out_mbps":     round(bitrate_out, 3),
                    }
                    writer.writerow(row)
                    # стало
                    if vmaf is None:
                        print(f"  crf={params['crf']} preset={params['preset']} vmaf=FAILED size={filesize_mb:.1f}MB")
                    else:
                        print(f"  crf={params['crf']} preset={params['preset']} vmaf={vmaf:.2f} size={filesize_mb:.1f}MB")

                finally:
                    os.unlink(out_path)  # удаляем временный файл


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: generate_dataset.py <output.csv> <video1.mp4> [video2.mp4 ...]")
        sys.exit(1)

    output_csv = sys.argv[1]
    videos     = sys.argv[2:]
    generate_dataset(videos, output_csv)