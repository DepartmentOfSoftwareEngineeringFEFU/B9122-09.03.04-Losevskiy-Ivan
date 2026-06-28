from pathlib import Path
import subprocess


# Соответствие пользовательских названий кодеков кодекам FFmpeg
CODEC_MAP = {
    # H.264 / AVC
    "h264": "libx264",
    "avc": "libx264",

    # H.265 / HEVC
    "h265": "libx265",
    "hevc": "libx265",

    # AV1
    "av1": "libsvtav1",

    # VP9
    "vp9": "libvpx-vp9",

    # VP8
    "vp8": "libvpx",

    # MPEG-4 Part 2
    "mpeg4": "mpeg4",
}


# Значения по умолчанию для каждого кодека
DEFAULT_PARAMS = {
    "h264": {
        "crf": 23,
        "preset": "medium",
        "aq-mode": 2,
        "bf": 3,
    },
    "hevc": {
        "crf": 28,
        "preset": "medium",
        "aq-mode": 2,
        "bf": 4,
    },
    "av1": {
        "crf": 35,
        "preset": 6,
    },
    "vp9": {
        "crf": 32,
        "b:v": 0,
    },
    "vp8": {
        "crf": 10,
        "b:v": "1M",
    },
    "mpeg4": {
        "q:v": 5,
    },
}


def compress_video(
    video_path: str,
    codec: str,
    params: dict | None = None,
    overwrite: bool = True,
    copy_audio: bool = True,
) -> str:
    """
    Сжимает видео через FFmpeg.

    Parameters
    ----------
    video_path : str
        Путь к видео.

    codec : str
        h264, hevc, av1, vp9, vp8, mpeg4.

    params : dict
        Параметры FFmpeg.
        Например:
        {
            "crf": 22,
            "preset": "slow",
            "aq-mode": 2,
            "bf": 4
        }

    overwrite : bool
        Перезаписывать выходной файл.

    copy_audio : bool
        Копировать аудио без перекодирования.

    Returns
    -------
    str
        Путь к сжатому файлу.
    """

    params = params or {}

    input_path = Path(video_path)

    if not input_path.exists():
        raise FileNotFoundError(
            f"Видео не найдено: {input_path}"
        )

    codec = codec.lower()

    if codec not in CODEC_MAP:
        raise ValueError(
            f"Неизвестный кодек '{codec}'. "
            f"Поддерживаемые кодеки: "
            f"{', '.join(sorted(CODEC_MAP.keys()))}"
        )

    ffmpeg_codec = CODEC_MAP[codec]

    output_path = (
        input_path.parent
        / f"{input_path.stem}_compressed{input_path.suffix}"
    )

    final_params = DEFAULT_PARAMS.get(codec, {}).copy()
    final_params.update(params)

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(input_path),
        "-c:v",
        ffmpeg_codec,
    ]

    for key, value in final_params.items():

        if value is None:
            continue

        ffmpeg_key = f"-{key}"

        if isinstance(value, bool):
            if value:
                cmd.append(ffmpeg_key)
        else:
            cmd.extend([ffmpeg_key, str(value)])

    if copy_audio:
        cmd.extend([
            "-c:a",
            "copy",
        ])
    else:
        cmd.extend([
            "-c:a",
            "aac",
            "-b:a",
            "128k",
        ])

    cmd.append("-y" if overwrite else "-n")
    cmd.append(str(output_path))

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Ошибка FFmpeg:\n{result.stderr}"
        )

    return str(output_path)


if __name__ == "__main__":

    compressed_file = compress_video(
        video_path="/home/tenshi/Code/Diplom/video/test.mp4",
        codec="h264",
        params={
            "crf": 21,
            "preset": "slow",
            "aq-mode": 2,
            "bf": 4,
        }
    )

    print(f"Сохранено: {compressed_file}")