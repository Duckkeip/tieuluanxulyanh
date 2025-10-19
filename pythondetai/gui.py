import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
from processor import load_images
from animator import create_gif


class GifApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("GIF Creator")
        self.root.geometry("800x600")
        self.root.config(bg="#f0f0f0")

        self.image_paths = []
        self.preview_labels = []

        self.create_widgets()

    def create_widgets(self):
        title = tk.Label(self.root, text="Tạo Ảnh Động (GIF) từ Nhiều Ảnh", font=("Arial", 18, "bold"), bg="#f0f0f0")
        title.pack(pady=20)

        btn_frame = tk.Frame(self.root, bg="#f0f0f0")
        btn_frame.pack(pady=10)

        upload_btn = tk.Button(btn_frame, text="📁 Chọn ảnh", command=self.upload_images, width=15, bg="#2196F3", fg="white")
        upload_btn.grid(row=0, column=0, padx=10)

        create_btn = tk.Button(btn_frame, text="🎞️ Tạo GIF", command=self.create_gif, width=15, bg="#4CAF50", fg="white")
        create_btn.grid(row=0, column=1, padx=10)

        self.preview_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.preview_frame.pack(pady=20)

    def upload_images(self):
        file_paths = filedialog.askopenfilenames(
            title="Chọn nhiều ảnh",
            filetypes=[("Ảnh", "*.png *.jpg *.jpeg *.bmp")]
        )

        if file_paths:
            self.image_paths = file_paths
            self.show_previews()

    def show_previews(self):
        for widget in self.preview_frame.winfo_children():
            widget.destroy()

        for idx, img_path in enumerate(self.image_paths):
            img = Image.open(img_path)
            img.thumbnail((100, 100))
            img_tk = ImageTk.PhotoImage(img)
            label = tk.Label(self.preview_frame, image=img_tk)
            label.image = img_tk
            label.grid(row=0, column=idx, padx=5, pady=5)

    def create_gif(self):
        if not self.image_paths:
            messagebox.showwarning("Chưa chọn ảnh", "Vui lòng chọn ít nhất 2 ảnh để tạo ảnh động.")
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".gif",
            filetypes=[("GIF files", "*.gif")],
            title="Lưu ảnh GIF"
        )

        if not save_path:
            return

        images = load_images(self.image_paths)
        create_gif(images, save_path)
        messagebox.showinfo("Thành công", f"Ảnh động đã được lưu tại:\n{save_path}")

    def run(self):
        self.root.mainloop()
