import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from io import BytesIO
from processor import load_images
from animator import create_gif


class GifApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("GIF Creator 🎞️")
        self.root.geometry("850x650")
        self.root.config(bg="#f0f0f0")

        self.image_paths = []
        self.preview_labels = []
        self.gif_label = None
        self.gif_frames = []
        self.gif_index = 0
        self.playing = False

        self.create_widgets()

    def create_widgets(self):
        title = tk.Label(self.root, text="Tạo Ảnh Động (GIF) từ Nhiều Ảnh", font=("Arial", 18, "bold"), bg="#f0f0f0")
        title.pack(pady=20)

        btn_frame = tk.Frame(self.root, bg="#f0f0f0")
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="📁 Chọn ảnh", command=self.upload_images, width=15, bg="#2196F3", fg="white").grid(row=0, column=0, padx=10)
        tk.Button(btn_frame, text="🎞️ Xem GIF", command=self.preview_gif, width=15, bg="#FF9800", fg="white").grid(row=0, column=1, padx=10)
        tk.Button(btn_frame, text="💾 Lưu GIF", command=self.save_gif, width=15, bg="#4CAF50", fg="white").grid(row=0, column=2, padx=10)
        self.ai_var = tk.BooleanVar()
        tk.Checkbutton(
            self.root,
            text="🧠 Dùng AI mượt hóa ảnh động",
            variable=self.ai_var,
            bg="#f0f0f0",
            font=("Arial", 11)
        ).pack()

        self.preview_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.preview_frame.pack(pady=20)

        self.gif_canvas = tk.Label(self.root, bg="#e0e0e0", width=400, height=300)
        self.gif_canvas.pack(pady=20)

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

    def preview_gif(self):
        if not self.image_paths:
            messagebox.showwarning("Chưa chọn ảnh", "Vui lòng chọn ít nhất 2 ảnh.")
            return

        images = load_images(self.image_paths)
        gif_buffer = create_gif(images, duration=200, smooth=self.ai_var.get(), num_inter_frames=2)

        gif = Image.open(gif_buffer)

        self.gif_frames = []
        try:
            while True:
                frame = gif.copy()
                frame = frame.resize((400, 300))
                self.gif_frames.append(ImageTk.PhotoImage(frame))
                gif.seek(len(self.gif_frames))
        except EOFError:
            pass

        if self.gif_frames:
            self.gif_index = 0
            self.playing = True
            self.play_gif()

    def play_gif(self):
        if not self.playing or not self.gif_frames:
            return
        frame = self.gif_frames[self.gif_index]
        self.gif_canvas.config(image=frame)
        self.gif_canvas.image = frame
        self.gif_index = (self.gif_index + 1) % len(self.gif_frames)
        self.root.after(150, self.play_gif)

    def save_gif(self):
        if not self.image_paths:
            messagebox.showwarning("Chưa chọn ảnh", "Vui lòng chọn ảnh trước.")
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".gif",
            filetypes=[("GIF files", "*.gif")],
            title="Lưu ảnh GIF"
        )
        if not save_path:
            return

        images = load_images(self.image_paths)
        gif_buffer = create_gif(images, smooth=self.ai_var.get(), num_inter_frames=2)
        with open(save_path, "wb") as f:
            f.write(gif_buffer.getvalue())
        messagebox.showinfo("Thành công", f"Ảnh động đã được lưu tại:\n{save_path}")

    def run(self):
        self.root.mainloop()
