# animator.py
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os
import math
import imageio.v2 as imageio
import cv2

def _draw_watermark(img: Image.Image, text: str, opacity: int = 180, margin=10):
    # kept for backward compatibility but GUI removed watermark; function remains unused
    if not text:
        return img
    img = img.convert("RGBA")
    txt = Image.new("RGBA", img.size, (255,255,255,0))
    draw = ImageDraw.Draw(txt)
    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except Exception:
        font = ImageFont.load_default()
    w, h = draw.textsize(text, font=font)
    x = img.width - w - margin
    y = img.height - h - margin
    draw.text((x, y), text, fill=(255,255,255,opacity), font=font)
    return Image.alpha_composite(img, txt).convert("RGB")

def _make_fade_frames(img1, img2, n):
    frames = []
    img1 = img1.convert("RGBA").resize(img2.size)
    img2 = img2.convert("RGBA").resize(img1.size)
    for i in range(1, n + 1):
        alpha = i / (n + 1)
        blended = Image.blend(img1, img2, alpha)
        frames.append(blended.convert("RGB"))
    return frames

def _make_slide_frames(img1, img2, n):
    frames = []
    img1 = img1.convert("RGBA").resize(img2.size)
    img2 = img2.convert("RGBA").resize(img1.size)
    w, h = img1.size
    for i in range(1, n + 1):
        alpha = i / (n + 1)
        offset = int(alpha * w)
        canvas = Image.new("RGBA", (w, h))
        canvas.paste(img1, (-offset, 0))
        canvas.paste(img2, (w - offset, 0), img2)
        frames.append(canvas.convert("RGB"))
    return frames

def create_gif(images, fps=10, effect='none', inter_frames=0, watermark_text=None, duration_ms=None):
    if len(images) < 1:
        raise ValueError("Cần ít nhất 1 ảnh.")
    if duration_ms is None:
        duration_ms = max(20, int(1000 / max(1, fps)))
    base_size = images[0].size
    norm_images = []
    for im in images:
        if im.size != base_size:
            norm_images.append(im.resize(base_size))
        else:
            norm_images.append(im)
    final_frames = []
    for i in range(len(norm_images) - 1):
        a = norm_images[i].convert("RGB")
        b = norm_images[i + 1].convert("RGB")
        if watermark_text:
            a = _draw_watermark(a, watermark_text)
        final_frames.append(a)
        if inter_frames > 0:
            if effect.lower() == 'fade':
                mids = _make_fade_frames(a, b, inter_frames)
            elif effect.lower() == 'slide':
                mids = _make_slide_frames(a, b, inter_frames)
            else:
                mids = [a.copy() for _ in range(inter_frames)]
            final_frames.extend(mids)
    last = norm_images[-1].convert("RGB")
    if watermark_text:
        last = _draw_watermark(last, watermark_text)
    final_frames.append(last)
    buffer = BytesIO()
    final_frames[0].save(
        buffer,
        format="GIF",
        save_all=True,
        append_images=final_frames[1:],
        duration=duration_ms,
        loop=0
    )
    buffer.seek(0)
    return buffer

def create_video(images, fps=30, effect='none', inter_frames=0, watermark_text=None, output_path='output.mp4'):
    """
    Tạo video MP4 từ danh sách PIL.Image.
    Sử dụng imageio (ffmpeg backend). output_path được trả về.
    """
    if len(images) < 1:
        raise ValueError("Cần ít nhất 1 ảnh để tạo video.")
    base_size = images[0].size
    norm_images = []
    for im in images:
        if im.size != base_size:
            norm_images.append(im.resize(base_size))
        else:
            norm_images.append(im)
    final_frames = []
    for i in range(len(norm_images) - 1):
        a = norm_images[i].convert("RGB")
        b = norm_images[i + 1].convert("RGB")
        if watermark_text:
            a = _draw_watermark(a, watermark_text)
        final_frames.append(a)
        if inter_frames > 0:
            if effect == 'fade':
                mids = _make_fade_frames(a, b, inter_frames)
            elif effect == 'slide':
                mids = _make_slide_frames(a, b, inter_frames)
            else:
                mids = []
            final_frames.extend(mids)
    last = norm_images[-1].convert("RGB")
    if watermark_text:
        last = _draw_watermark(last, watermark_text)
    final_frames.append(last)
    # write with imageio
    writer = imageio.get_writer(output_path, fps=fps)
    for frame in final_frames:
        # convert PIL Image to numpy array
        writer.append_data(imageio.asarray(frame))
    writer.close()
    return output_path

def extract_frames_from_video(video_path: str, target_fps: int, max_duration: float, output_dir: str):
    """
    Extract frames from a video at a specified target_fps for up to max_duration seconds.
    Saves images into output_dir and returns list of saved file paths.
    Uses accurate timestamp sampling (not simple every Nth frame).
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError("Video không tồn tại.")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError("Không thể mở video.")
    orig_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    orig_duration = frame_count / orig_fps if orig_fps > 0 else 0
    duration = min(orig_duration, max_duration)
    if duration <= 0:
        cap.release()
        raise ValueError("Video có thời lượng không hợp lệ.")
    os.makedirs(output_dir, exist_ok=True)
    timestamps = []
    step = 1.0 / float(target_fps)
    t = 0.0
    while t < duration - 1e-6:
        timestamps.append(t)
        t += step
    # Ensure last frame at duration - small epsilon
    if len(timestamps) == 0:
        timestamps = [0.0]
    saved_paths = []
    idx = 0
    for ts in timestamps:
        # set position by time in milliseconds
        cap.set(cv2.CAP_PROP_POS_MSEC, ts * 1000.0)
        ret, frame = cap.read()
        if not ret:
            # try to read by frame index fallback
            frame_index = int(min(math.floor(ts * orig_fps), frame_count - 1))
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ret, frame = cap.read()
            if not ret:
                continue
        # save as PNG
        filename = f"frame_{idx:04d}.png"
        outpath = os.path.join(output_dir, filename)
        cv2.imwrite(outpath, frame)
        saved_paths.append(outpath)
        idx += 1
    cap.release()
    return {
        "saved_paths": saved_paths,
        "requested_fps": target_fps,
        "duration_used": duration,
        "orig_fps": orig_fps,
        "orig_duration": orig_duration
    }
