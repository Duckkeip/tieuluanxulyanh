# gui.py
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from processor import load_images
from animator import create_gif, create_video, extract_frames_from_video
import cv2
import threading
import time
import os

MAX_EXTRACT_SECONDS = 15.0

class GifApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("GIF & Video Tool")
        self.root.geometry("1200x760")
        self.root.config(bg="#f7f7f7")

        # Shared
        self.image_paths = []
        self.gif_frames = []
        self.gif_index = 0
        self.playing = False

        # Video preview variables
        self.video_running = False
        self.video_paused = False
        self.video_thread = None
        self.video_path = None

        # Extract tab variables
        self.import_video_path = None
        self.extract_saved = []

        self.create_widgets()

    def create_widgets(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Tab 1: GIF & Video Creator
        tab1 = tk.Frame(notebook, bg="#f7f7f7")
        notebook.add(tab1, text="GIF & Video Creator")

        # Control frame
        control_frame = tk.Frame(tab1, bg="#f7f7f7")
        control_frame.pack(pady=8)

        tk.Button(control_frame, text="📁 Chọn ảnh", command=self.upload_images, width=14).grid(row=0, column=0, padx=6)
        tk.Button(control_frame, text="🎞️ Xem GIF", command=self.preview_gif, width=14).grid(row=0, column=1, padx=6)
        tk.Button(control_frame, text="💾 Lưu GIF", command=self.save_gif, width=14).grid(row=0, column=2, padx=6)
        tk.Button(control_frame, text="🎬 Tạo Video", command=self.create_video_preview, width=14).grid(row=0, column=3, padx=6)
        tk.Button(control_frame, text="🧹 Xóa danh sách", command=self.clear_list, width=12).grid(row=0, column=4, padx=6)

        # Options
        options_frame = tk.Frame(tab1, bg="#f7f7f7")
        options_frame.pack(pady=6, fill="x", padx=20)

        tk.Label(options_frame, text="FPS:", bg="#f7f7f7").grid(row=0, column=0, sticky="w")
        self.fps_var = tk.IntVar(value=10)
        tk.Spinbox(options_frame, from_=1, to=60, textvariable=self.fps_var, width=6).grid(row=0, column=1, padx=(4,20))
        tk.Label(options_frame, text="Hiệu ứng:", bg="#f7f7f7").grid(row=0, column=2, sticky="w")
        self.effect_var = tk.StringVar(value="none")
        tk.OptionMenu(options_frame, self.effect_var, "none", "fade", "slide").grid(row=0, column=3, padx=(4,20))
        tk.Label(options_frame, text="Khung trung gian:", bg="#f7f7f7").grid(row=0, column=4, sticky="w")
        self.inter_var = tk.IntVar(value=0)
        tk.Spinbox(options_frame, from_=0, to=30, textvariable=self.inter_var, width=6).grid(row=0, column=5, padx=(4,20))

        # Preview thumbnails (scrollable)
        preview_container = tk.Frame(tab1, bg="#fff", bd=1, relief="sunken")
        preview_container.pack(pady=10, padx=20, fill="x")
        self.preview_canvas = tk.Canvas(preview_container, bg="#fff", height=140, highlightthickness=0)
        self.preview_canvas.pack(side="left", fill="x", expand=True)
        scrollbar_x = tk.Scrollbar(preview_container, orient="horizontal", command=self.preview_canvas.xview)
        scrollbar_x.pack(side="bottom", fill="x")
        self.preview_canvas.configure(xscrollcommand=scrollbar_x.set)
        self.thumb_frame = tk.Frame(self.preview_canvas, bg="#fff")
        self.preview_canvas.create_window((0,0), window=self.thumb_frame, anchor="nw")
        self.thumb_frame.bind("<Configure>", lambda e: self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox("all")))

        # GIF + Logo luôn hiển thị
        preview_area = tk.Frame(tab1, bg="#f7f7f7")
        preview_area.pack(pady=10, fill="both", expand=True)

        # Khung xem GIF bên trái
        self.gif_canvas = tk.Label(preview_area, bg="#e0e0e0", width=560, height=420)
        self.gif_canvas.grid(row=0, column=0, padx=12, pady=8, sticky="nsew")


        # ------------------------
        # Tab 2: Import Video -> Extract Frames
        tab2 = tk.Frame(notebook, bg="#f7f7f7")
        notebook.add(tab2, text="Import Video → Extract Frames")

        # Controls for import tab
        vctrl = tk.Frame(tab2, bg="#f7f7f7")
        vctrl.pack(pady=8, fill="x", padx=12)
        tk.Button(vctrl, text="📁 Chọn Video", command=self.select_import_video, width=16).grid(row=0, column=0, padx=6)
        tk.Label(vctrl, text="Target FPS:", bg="#f7f7f7").grid(row=0, column=1, sticky="w")
        self.target_fps_var = tk.IntVar(value=24)
        ttk.Combobox(vctrl, textvariable=self.target_fps_var, values=(12,24,60), width=6, state="readonly").grid(row=0, column=2, padx=6)
        tk.Label(vctrl, text="Thời lượng (giây, ≤15):", bg="#f7f7f7").grid(row=0, column=3, sticky="w")
        self.extract_duration_var = tk.IntVar(value=5)
        tk.Spinbox(vctrl, from_=1, to=int(MAX_EXTRACT_SECONDS), textvariable=self.extract_duration_var, width=6).grid(row=0, column=4, padx=6)
        tk.Button(vctrl, text="📤 Chọn Thư Mục Lưu", command=self.choose_output_folder, width=16).grid(row=0, column=5, padx=6)
        self.output_folder_label = tk.Label(vctrl, text="(Chưa chọn thư mục)", bg="#f7f7f7")
        self.output_folder_label.grid(row=1, column=0, columnspan=6, sticky="w", padx=6, pady=(6,0))

        tk.Button(tab2, text="🎯 Xuất frames", command=self.start_extract_frames, width=20).pack(pady=8)

        # Thumbnails area for extracted frames
        extract_preview_container = tk.Frame(tab2, bg="#fff", bd=1, relief="sunken")
        extract_preview_container.pack(padx=12, pady=8, fill="both", expand=True)
        self.extract_canvas = tk.Canvas(extract_preview_container, bg="#fff", height=300)
        self.extract_canvas.pack(side="left", fill="both", expand=True)
        extract_scroll = tk.Scrollbar(extract_preview_container, orient="horizontal", command=self.extract_canvas.xview)
        extract_scroll.pack(side="bottom", fill="x")
        self.extract_canvas.configure(xscrollcommand=extract_scroll.set)
        self.extract_thumb_frame = tk.Frame(self.extract_canvas, bg="#fff")
        self.extract_canvas.create_window((0,0), window=self.extract_thumb_frame, anchor="nw")
        self.extract_thumb_frame.bind("<Configure>", lambda e: self.extract_canvas.configure(scrollregion=self.extract_canvas.bbox("all")))

    # ----------------- Tab1 functions (GIF/Video) -----------------
    def upload_images(self):
        file_paths = filedialog.askopenfilenames(title="Chọn nhiều ảnh", filetypes=[("Ảnh", "*.png *.jpg *.jpeg *.bmp")])
        if file_paths:
            self.image_paths = list(file_paths)
            self.show_previews()

    def show_previews(self):
        for w in self.thumb_frame.winfo_children():
            w.destroy()
        for idx, path in enumerate(self.image_paths):
            try:
                img = Image.open(path)
                img.thumbnail((120,120))
                tkimg = ImageTk.PhotoImage(img)
                lbl = tk.Label(self.thumb_frame, image=tkimg, bg="#fff")
                lbl.image = tkimg
                lbl.grid(row=0, column=idx, padx=6, pady=6)
            except Exception as e:
                print("Lỗi mở ảnh:", path, e)
        self.thumb_frame.update_idletasks()
        self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox("all"))

    def preview_gif(self):
        if not self.image_paths:
            messagebox.showwarning("Chưa chọn ảnh", "Vui lòng chọn ít nhất 1 ảnh.")
            return
        images = load_images(self.image_paths)
        try:
            gif_buffer = create_gif(images, fps=self.fps_var.get(), effect=self.effect_var.get(), inter_frames=self.inter_var.get())
        except Exception as e:
            messagebox.showerror("Lỗi tạo GIF", str(e))
            return
        self.gif_frames = []
        from PIL import Image as PILImage
        try:
            gif = PILImage.open(gif_buffer)
            while True:
                f = gif.copy()
                f.thumbnail((540,420))
                self.gif_frames.append(ImageTk.PhotoImage(f.convert("RGBA")))
                gif.seek(len(self.gif_frames))
        except EOFError:
            pass
        if self.gif_frames:
            self.gif_index = 0
            self.playing = True
            self._play_gif_loop()
        else:
            messagebox.showinfo("Không có khung", "Không thể tạo khung GIF để xem trước.")

    def _play_gif_loop(self):
        if not self.playing or not self.gif_frames:
            return
        frame = self.gif_frames[self.gif_index]
        self.gif_canvas.config(image=frame)
        self.gif_canvas.image = frame
        self.gif_index = (self.gif_index + 1) % len(self.gif_frames)
        ms = max(20, int(1000 / max(1, self.fps_var.get())))
        self.root.after(ms, self._play_gif_loop)

    def save_gif(self):
        if not self.image_paths:
            messagebox.showwarning("Chưa chọn ảnh", "Vui lòng chọn ảnh trước.")
            return
        save_path = filedialog.asksaveasfilename(defaultextension=".gif", filetypes=[("GIF files", "*.gif")])
        if not save_path:
            return
        images = load_images(self.image_paths)
        try:
            gif_buffer = create_gif(images, fps=self.fps_var.get(), effect=self.effect_var.get(), inter_frames=self.inter_var.get())
            with open(save_path, "wb") as f:
                f.write(gif_buffer.getvalue())
            messagebox.showinfo("Thành công", f"Đã lưu GIF tại:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Lỗi lưu GIF", str(e))

    def create_video_preview(self):
        if not self.image_paths:
            messagebox.showwarning("Chưa chọn ảnh", "Vui lòng chọn ảnh trước.")
            return

        images = load_images(self.image_paths)
        self.video_path = "temp_video.mp4"

        try:
            create_video(images, fps=self.fps_var.get(),
                         effect=self.effect_var.get(),
                         inter_frames=self.inter_var.get(),
                         output_path=self.video_path)
        except Exception as e:
            messagebox.showerror("Lỗi tạo video", str(e))
            return

        # Mở cửa sổ preview video riêng
        self.open_video_window(self.video_path)

    def open_video_window(self, video_path):
        if not os.path.exists(video_path):
            messagebox.showerror("Lỗi", "Không tìm thấy file video.")
            return

        win = tk.Toplevel(self.root)
        win.title("Xem trước Video")
        win.geometry("800x600")
        win.config(bg="#222")

        video_label = tk.Label(win, bg="#000")
        video_label.pack(padx=10, pady=10, fill="both", expand=True)

        controls = tk.Frame(win, bg="#333")
        controls.pack(fill="x", pady=10)

        # Biến điều khiển video
        cap = cv2.VideoCapture(video_path)
        paused = False
        running = True
        speed_factor = 1.0  # tốc độ mặc định (1x)

        # Nhãn hiển thị tốc độ
        speed_label = tk.Label(controls, text="Tốc độ: 1.0x", bg="#333", fg="white", width=12)
        speed_label.pack(side="right", padx=10)

        def update_speed_label():
            speed_label.config(text=f"Tốc độ: {speed_factor:.1f}x")

        def play_video():
            nonlocal paused
            paused = False

        def pause_video():
            nonlocal paused
            paused = True

        def skip_video():
            nonlocal cap
            pos = cap.get(cv2.CAP_PROP_POS_MSEC)
            cap.set(cv2.CAP_PROP_POS_MSEC, pos + 5000)

        def toggle_fullscreen():
            win.attributes("-fullscreen", not win.attributes("-fullscreen"))

        def increase_speed():
            nonlocal speed_factor
            if speed_factor < 4.0:
                speed_factor *= 2
                update_speed_label()

        def decrease_speed():
            nonlocal speed_factor
            if speed_factor > 0.25:
                speed_factor /= 2
                update_speed_label()

        # Các nút điều khiển
        tk.Button(controls, text="▶️ Phát", width=10, command=play_video).pack(side="left", padx=5)
        tk.Button(controls, text="⏸ Tạm dừng", width=10, command=pause_video).pack(side="left", padx=5)
        tk.Button(controls, text="⏩ Tua +5s", width=10, command=skip_video).pack(side="left", padx=5)
        tk.Button(controls, text="⏪ 0.5x", width=8, command=decrease_speed).pack(side="left", padx=5)
        tk.Button(controls, text="⏩ 2x", width=8, command=increase_speed).pack(side="left", padx=5)
        tk.Button(controls, text="🔍 Phóng to", width=10, command=toggle_fullscreen).pack(side="right", padx=5)

        def update_frame():
            nonlocal running
            if not running:
                return
            if not paused:
                ret, frame = cap.read()
                if not ret:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # lặp lại
                    ret, frame = cap.read()
                if ret:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame)
                    img.thumbnail((760, 540))
                    imgtk = ImageTk.PhotoImage(img)
                    video_label.config(image=imgtk)
                    video_label.image = imgtk

            # Thay đổi tốc độ bằng cách điều chỉnh khoảng delay giữa các frame
            delay = int(30 / speed_factor)  # 30ms là khoảng ~33fps
            win.after(max(1, delay), update_frame)

        def on_close():
            nonlocal running
            running = False
            cap.release()
            win.destroy()

        win.protocol("WM_DELETE_WINDOW", on_close)
        update_frame()

    # ----------------- Video preview (Tab1) -----------------
    def play_video(self):
        if not self.video_path or not os.path.exists(self.video_path):
            messagebox.showinfo("Chưa có video", "Hãy tạo video trước.")
            return
        if self.video_running:
            self.video_paused = False
            return
        self.video_running = True
        self.video_paused = False
        self.video_thread = threading.Thread(target=self._video_loop, daemon=True)
        self.video_thread.start()

    def _video_loop(self):
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            messagebox.showerror("Lỗi", "Không mở được file video.")
            self.video_running = False
            return
        orig_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        while cap.isOpened() and self.video_running:
            if self.video_paused:
                time.sleep(0.05)
                continue
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            img.thumbnail((560,420))
            imgtk = ImageTk.PhotoImage(img)
            # update on main thread via .after
            self.video_canvas.after(0, lambda im=imgtk: self._update_video_canvas(im))
            # sleep according to original fps
            time.sleep(1.0 / max(1.0, orig_fps))
        cap.release()
        self.video_running = False

    def _update_video_canvas(self, imgtk):
        for w in self.video_canvas.winfo_children():
            w.destroy()
            # Hiển thị khung hình video
        self.video_canvas.config(image=imgtk)
        self.video_canvas.image = imgtk

    def pause_video(self):
        self.video_paused = not self.video_paused

    def skip_video(self):
        # naive skip: stop and restart reader + jump approx 5s forward by setting CAP_PROP_POS_MSEC
        if not self.video_path or not os.path.exists(self.video_path):
            return
        # if not running, just start playing
        if not self.video_running:
            self.play_video()
            return
        # set flag to pause then reposition by reopening capture in thread loop - not trivial to do safely here
        # For simplicity show message: skip implemented as restart from +5s when thread reads position
        # We'll just pause and show info (robust seek needs more complex thread-safe design)
        self.video_paused = True
        messagebox.showinfo("Tua", "Tua hiện tại thực hiện bằng việc dừng rồi phát lại tại vị trí mong muốn (tạm thời giới hạn).")

    def toggle_fullscreen(self):
        self.root.attributes("-fullscreen", not self.root.attributes("-fullscreen"))

    def clear_list(self):
        self.image_paths = []
        for widget in self.thumb_frame.winfo_children():
            widget.destroy()
        self.gif_canvas.config(image="", text="")
        self.video_canvas.config(image="", text="(Chưa có video)")

    # ----------------- Tab2 functions (Import video & extract) -----------------
    def select_import_video(self):
        path = filedialog.askopenfilename(title="Chọn file video", filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv *.webm"), ("All files", "*.*")])
        if path:
            self.import_video_path = path
            # try to get video duration
            cap = cv2.VideoCapture(path)
            if cap.isOpened():
                fps = cap.get(cv2.CAP_PROP_FPS) or 0
                frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
                dur = frames / fps if fps > 0 else 0
                cap.release()
            else:
                dur = 0
            # clamp displayed max
            allowed = min(dur, MAX_EXTRACT_SECONDS)
            self.extract_duration_var.set(int(min(allowed, self.extract_duration_var.get() or 1)))
            messagebox.showinfo("Đã chọn video", f"Video: {os.path.basename(path)}\nDuration: {dur:.2f}s (sẽ lấy tối đa {allowed:.2f}s)")
        else:
            self.import_video_path = None

    def choose_output_folder(self):
        folder = filedialog.askdirectory(title="Chọn thư mục lưu frames")
        if folder:
            self.output_folder = folder
            self.output_folder_label.config(text=self.output_folder)
        else:
            self.output_folder = None
            self.output_folder_label.config(text="(Chưa chọn thư mục)")

    def start_extract_frames(self):
        if not self.import_video_path:
            messagebox.showwarning("Chưa chọn video", "Vui lòng chọn file video trước.")
            return
        if not hasattr(self, "output_folder") or not self.output_folder:
            messagebox.showwarning("Chưa chọn thư mục lưu", "Vui lòng chọn thư mục lưu frames.")
            return
        target_fps = int(self.target_fps_var.get())
        duration_requested = int(self.extract_duration_var.get())
        duration = min(duration_requested, MAX_EXTRACT_SECONDS)
        # run in thread
        t = threading.Thread(target=self._do_extract_frames, args=(self.import_video_path, target_fps, duration, self.output_folder), daemon=True)
        t.start()

    def _do_extract_frames(self, video_path, target_fps, duration, output_folder):
        try:
            info = extract_frames_from_video(video_path, target_fps, duration, output_folder)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Lỗi extract", str(e)))
            return
        saved = info.get("saved_paths", [])
        self.extract_saved = saved
        # update UI thumbnails on main thread
        self.root.after(0, lambda: self._show_extracted_thumbnails(saved))
        self.root.after(0, lambda: messagebox.showinfo("Hoàn tất", f"Đã xuất {len(saved)} ảnh vào:\n{output_folder}"))

    def _show_extracted_thumbnails(self, paths):
        for w in self.extract_thumb_frame.winfo_children():
            w.destroy()
        for idx, p in enumerate(paths):
            try:
                img = Image.open(p)
                img.thumbnail((160, 120))
                tkimg = ImageTk.PhotoImage(img)
                lbl = tk.Label(self.extract_thumb_frame, image=tkimg, bg="#fff")
                lbl.image = tkimg
                lbl.grid(row=0, column=idx, padx=6, pady=6)
            except Exception as e:
                print("Không thể mở thumb:", p, e)
        self.extract_thumb_frame.update_idletasks()
        self.extract_canvas.configure(scrollregion=self.extract_canvas.bbox("all"))

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = GifApp()
    app.run()
