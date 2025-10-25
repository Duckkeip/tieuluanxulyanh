from PIL import Image

def create_gif(images, duration=100):
    """
    Tạo ảnh GIF từ danh sách ảnh (không lưu file, chỉ trả về ảnh GIF trong RAM).
    duration: thời gian hiển thị mỗi khung (ms)
    """
    if len(images) < 2:
        raise ValueError("Cần ít nhất 2 ảnh để tạo ảnh động.")

    from io import BytesIO
    buffer = BytesIO()
    images[0].save(
        buffer,
        format='GIF',
        save_all=True,
        append_images=images[1:],
        duration=duration,
        loop=0
    )
    buffer.seek(0)
    return buffer  # trả về dữ liệu GIF
