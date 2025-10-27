# ai_interpolator.py
from PIL import Image
import numpy as np
import cv2

def interpolate_frames(img1: Image.Image, img2: Image.Image, num_frames=1):
    """
    Giả lập tạo khung trung gian giữa img1 và img2 (không dùng AI thật).
    Dùng phép hòa trộn pixel tuyến tính để tạo hiệu ứng chuyển động mượt.
    Tự động resize ảnh thứ hai để khớp kích thước ảnh thứ nhất.
    """
    # Chuyển sang RGB và resize cho khớp
    img1 = img1.convert("RGB")
    img2 = img2.convert("RGB").resize(img1.size)

    # Chuyển sang mảng numpy
    frame1 = np.array(img1, dtype=np.float32)
    frame2 = np.array(img2, dtype=np.float32)

    interpolated = []
    for i in range(1, num_frames + 1):
        alpha = i / (num_frames + 1)
        blended = cv2.addWeighted(frame1, 1 - alpha, frame2, alpha, 0)
        blended = np.clip(blended, 0, 255).astype(np.uint8)
        interpolated.append(Image.fromarray(blended))

    return interpolated
