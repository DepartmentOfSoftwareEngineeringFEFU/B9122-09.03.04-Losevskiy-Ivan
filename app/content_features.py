import cv2
import numpy as np
from scipy.stats import entropy as scipy_entropy


FRAME_STEP = 10       # анализировать каждый 10-й кадр
MAX_FRAMES = 500      # максимум кадров для анализа
RESIZE_FACTOR = 0.5   # уменьшение разрешения


def calculate_entropy(gray):
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    hist = hist.ravel()

    hist_sum = hist.sum()
    if hist_sum == 0:
        return 0.0

    hist /= hist_sum
    hist = hist[hist > 0]

    return float(scipy_entropy(hist, base=2))


def determine_content_type(
    spatial_information,
    motion_magnitude,
    texture_complexity,
    entropy_value
):
    if motion_magnitude > 20:
        return "high_motion"

    if texture_complexity < 50 and entropy_value < 5:
        return "cartoon_animation"

    if spatial_information > 100 and texture_complexity > 300:
        return "high_detail"

    return "static"


def analyze_video(video_path):
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    spatial_values = []
    temporal_values = []
    noise_values = []
    texture_values = []
    motion_values = []
    entropy_values = []

    prev_gray = None

    scene_cuts = 0
    processed_frames = 0
    frame_idx = 0

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        frame_idx += 1

        if frame_idx % FRAME_STEP != 0:
            continue

        processed_frames += 1

        if processed_frames > MAX_FRAMES:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if RESIZE_FACTOR != 1.0:
            gray = cv2.resize(
                gray,
                None,
                fx=RESIZE_FACTOR,
                fy=RESIZE_FACTOR,
                interpolation=cv2.INTER_AREA
            )

        # ==================================================
        # Spatial Information
        # ==================================================

        sobel_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)

        gradient = cv2.magnitude(sobel_x, sobel_y)

        spatial_values.append(float(np.std(gradient)))

        # ==================================================
        # Noise Level
        # ==================================================

        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        noise = np.mean(
            np.abs(
                gray.astype(np.float32) -
                blurred.astype(np.float32)
            )
        )

        noise_values.append(float(noise))

        # ==================================================
        # Texture Complexity
        # ==================================================

        texture = cv2.Laplacian(
            gray,
            cv2.CV_32F
        ).var()

        texture_values.append(float(texture))

        # ==================================================
        # Entropy
        # ==================================================

        entropy_values.append(calculate_entropy(gray))

        # ==================================================
        # Temporal Information
        # Motion Magnitude
        # Scene Cut Frequency
        # ==================================================

        if prev_gray is not None:

            diff = cv2.absdiff(gray, prev_gray)

            temporal_information_frame = float(np.std(diff))
            motion_magnitude_frame = float(np.mean(diff))

            temporal_values.append(temporal_information_frame)
            motion_values.append(motion_magnitude_frame)

            if motion_magnitude_frame > 40:
                scene_cuts += 1

        prev_gray = gray

    cap.release()

    spatial_information = (
        float(np.mean(spatial_values))
        if spatial_values else 0.0
    )

    temporal_information = (
        float(np.mean(temporal_values))
        if temporal_values else 0.0
    )

    scene_cut_frequency = (
        scene_cuts / processed_frames
        if processed_frames else 0.0
    )

    noise_level = (
        float(np.mean(noise_values))
        if noise_values else 0.0
    )

    texture_complexity = (
        float(np.mean(texture_values))
        if texture_values else 0.0
    )

    motion_magnitude = (
        float(np.mean(motion_values))
        if motion_values else 0.0
    )

    entropy_value = (
        float(np.mean(entropy_values))
        if entropy_values else 0.0
    )

    content_type = determine_content_type(
        spatial_information,
        motion_magnitude,
        texture_complexity,
        entropy_value
    )

    return (
        spatial_information,
        temporal_information,
        scene_cut_frequency,
        noise_level,
        texture_complexity,
        motion_magnitude,
        entropy_value,
        content_type
    )


if __name__ == "__main__":
    result = analyze_video("/home/tenshi/Code/Diplom/video/test.mp4")

    print("\nContent Features:")
    print(f"Spatial Information : {result[0]:.2f}")
    print(f"Temporal Information: {result[1]:.2f}")
    print(f"Scene Cut Frequency : {result[2]:.4f}")
    print(f"Noise Level         : {result[3]:.2f}")
    print(f"Texture Complexity  : {result[4]:.2f}")
    print(f"Motion Magnitude    : {result[5]:.2f}")
    print(f"Entropy             : {result[6]:.2f}")
    print(f"Content Type        : {result[7]}")