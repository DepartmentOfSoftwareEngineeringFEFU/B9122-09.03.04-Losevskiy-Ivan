#!/usr/bin/env bash
# извлекает метаданные через ffprobe

VIDEO="$1"
OUTPUT="${2:-metadata.json}"

if [[ -z "$VIDEO" ]]; then
    echo "Usage: $0 <video> [output.json]" >&2
    exit 1
fi

if [[ ! -f "$VIDEO" ]]; then
    echo "Error: file not found: $VIDEO" >&2
    exit 1
fi

ffprobe \
    -v quiet \
    -print_format json \
    -show_format \
    -show_streams \
    "$VIDEO" > "$OUTPUT"

echo "Saved to $OUTPUT"