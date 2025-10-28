# processor.py
from PIL import Image

def load_images(image_paths):
    """
    Trả về danh sách PIL.Image đã convert sang RGB.
    """
    images = []
    for path in image_paths:
        img = Image.open(path).convert("RGB")
        images.append(img)
    return images
