from PIL import Image
from ai import interpolate_frames

def create_gif(images, duration=100, smooth=False, num_inter_frames=1):
    """
    Tạo ảnh GIF từ danh sách ảnh.
    Nếu smooth=True → thêm khung trung gian để ảnh mượt hơn.
    """
    if len(images) < 2:
        raise ValueError("Cần ít nhất 2 ảnh để tạo ảnh động.")

    final_frames = []
    for i in range(len(images) - 1):
        final_frames.append(images[i])
        if smooth:
            mids = interpolate_frames(images[i], images[i + 1], num_frames=num_inter_frames)
            final_frames.extend(mids)
    final_frames.append(images[-1])

    from io import BytesIO
    buffer = BytesIO()
    final_frames[0].save(
        buffer,
        format="GIF",
        save_all=True,
        append_images=final_frames[1:],
        duration=duration,
        loop=0
    )
    buffer.seek(0)
    return buffer
