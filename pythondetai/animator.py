def create_gif(images, save_path, duration=100):# thời gian giua cac anh, theo ms
    """
    Tạo ảnh GIF từ danh sách ảnh.
    duration: thời gian hiển thị mỗi khung (ms)
    """
    if len(images) < 2:
        raise ValueError("Cần ít nhất 2 ảnh để tạo ảnh động.")

    first_img = images[0]
    first_img.save(
        save_path,
        save_all=True,
        append_images=images[1:],
        duration=duration,
        loop=0
    )
