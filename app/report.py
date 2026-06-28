"""
video_similarity.py

Модуль для оценки схожести двух видео с помощью SSIM.
Возвращаемое значение находится в диапазоне [0; 1].
"""

import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim


def calculate_video_similarity(video1_path: str, video2_path: str) -> float:
    """
    Вычисляет средний SSIM между двумя видео.

    Parameters
    ----------
    video1_path : str
        Путь к первому видео.

    video2_path : str
        Путь ко второму видео.

    Returns
    -------
    float
        Среднее значение SSIM от 0 до 1.
    """

    cap1 = cv2.VideoCapture(video1_path)
    cap2 = cv2.VideoCapture(video2_path)

    if not cap1.isOpened():
        raise FileNotFoundError(f"Не удалось открыть видео: {video1_path}")

    if not cap2.isOpened():
        raise FileNotFoundError(f"Не удалось открыть видео: {video2_path}")

    scores = []

    while True:
        ret1, frame1 = cap1.read()
        ret2, frame2 = cap2.read()

        if not ret1 or not ret2:
            break

        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

        if gray1.shape != gray2.shape:
            frame2 = cv2.resize(
                gray2,
                (gray1.shape[1], gray1.shape[0]),
                interpolation=cv2.INTER_AREA,
            )
        else:
            frame2 = gray2

        score = ssim(gray1, frame2)
        scores.append(score)

    cap1.release()
    cap2.release()

    if not scores:
        return 0.0

    return float(np.mean(scores))