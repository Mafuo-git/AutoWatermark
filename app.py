from __future__ import annotations

import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import colorchooser, filedialog, messagebox, ttk

from PIL import Image, ImageTk

from processing import collect_folder, create_preview, process_batch
from watermark import WatermarkSettings, available_fonts, render_overlay


class AutoWatermarkApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("AutoWatermark")
        self.root.geometry("1180x800")
        self.root.minsize(1000, 690)
        self.root.configure(bg="#f4f6fb")
        self.files: list[Path] = []
        self.source_root: Path | None = None
        self.preview_image: Image.Image | None = None
        self.preview_source_path: Path | None = None
        self.preview_photo: ImageTk.PhotoImage | None = None
        self.preview_bounds = (0, 0, 1, 1)
        self.dragging = False
        self.logo_path = tk.StringVar()
        self.text = tk.StringVar(value="© Your Name")
        self.text_color = "#FFFFFF"
        self.background_color = "#111827"
        self.font_options = available_fonts()
        self.font_name = tk.StringVar(value=next((name for name, _ in self.font_options if name.lower() == "arial"), self.font_options[0][0]))
        self.font_path = tk.StringVar(value=next((path for name, path in self.font_options if name == self.font_name.get()), ""))
        self.font_scale = tk.DoubleVar(value=4.5)
        self.opacity = tk.DoubleVar(value=82)
        self.position_x = 0.94
        self.position_y = 0.94
        self.overwrite = tk.BooleanVar(value=False)
        self.output_folder = tk.StringVar()
        self.status = tk.StringVar(value="Add photos or select a folder to get started.")
        self.logo_path.trace_add("write", lambda *_args: self._draw_preview())
        self._build_ui()
        self._draw_preview()

    def _build_ui(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#f4f6fb")
        style.configure("Card.TFrame", background="#ffffff")
        style.configure("TLabel", background="#f4f6fb", foreground="#172033", font=("Segoe UI", 9))
        style.configure("Card.TLabel", background="#ffffff", foreground="#172033", font=("Segoe UI", 9))
        style.configure("Title.TLabel", font=("Segoe UI Semibold", 18), foreground="#14213d")
        style.configure("Section.TLabel", font=("Segoe UI Semibold", 10), foreground="#1d3557", background="#ffffff")
        style.configure("TButton", font=("Segoe UI", 9), padding=(9, 6))
        style.configure("Accent.TButton", background="#3157d5", foreground="#ffffff", font=("Segoe UI Semibold", 10))
        style.map("Accent.TButton", background=[("active", "#2446b8")])
        style.configure("TCheckbutton", background="#ffffff")
        style.configure("TCombobox", padding=4)
        style.configure("Horizontal.TProgressbar", troughcolor="#e7ebf3", background="#3157d5")

        header = ttk.Frame(self.root, padding=(22, 16, 22, 8))
        header.pack(fill="x")
        ttk.Label(header, text="AutoWatermark", style="Title.TLabel").pack(side="left")
        ttk.Label(header, text="Watermark your photos with ease", foreground="#667085").pack(side="left", padx=14, pady=(5, 0))
        ttk.Label(header, text="Windows · processed locally", foreground="#667085").pack(side="right", pady=(5, 0))

        main = ttk.Frame(self.root, padding=(18, 8, 18, 12))
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=1, minsize=330)
        main.columnconfigure(1, weight=2, minsize=520)
        main.rowconfigure(0, weight=1)

        left = ttk.Frame(main, style="Card.TFrame", padding=14)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        right = ttk.Frame(main, style="Card.TFrame", padding=14)
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        left.grid_rowconfigure(2, weight=1)
        left.grid_columnconfigure(0, weight=1)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(3, weight=1)

        ttk.Label(left, text="1  ·  SOURCE PHOTOS", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        source_actions = ttk.Frame(left, style="Card.TFrame")
        source_actions.grid(row=1, column=0, sticky="ew", pady=(8, 6))
        ttk.Button(source_actions, text="Choose folder", command=self._choose_folder).pack(side="left", padx=(0, 6))
        ttk.Button(source_actions, text="Add photos", command=self._choose_files).pack(side="left")
        self.file_list = tk.Listbox(left, height=8, selectmode=tk.EXTENDED, relief="flat", borderwidth=0, highlightthickness=1, highlightbackground="#dce2ed", font=("Segoe UI", 9), activestyle="none")
        self.file_list.grid(row=2, column=0, sticky="nsew")
        self.file_list.bind("<<ListboxSelect>>", lambda _event: self._draw_preview())
        file_buttons = ttk.Frame(left, style="Card.TFrame")
        file_buttons.grid(row=3, column=0, sticky="ew", pady=(5, 12))
        ttk.Button(file_buttons, text="Remove selected", command=self._remove_selected).pack(side="left")
        ttk.Button(file_buttons, text="Clear all", command=self._clear_files).pack(side="left", padx=6)

        ttk.Label(left, text="2  ·  OUTPUT", style="Section.TLabel").grid(row=4, column=0, sticky="nw", pady=(0, 7))
        destination = ttk.Frame(left, style="Card.TFrame")
        destination.grid(row=5, column=0, sticky="ew")
        ttk.Checkbutton(destination, text="Replace original files", variable=self.overwrite, command=self._toggle_output).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 7))
        ttk.Label(destination, text="Or save copies to an output folder:", style="Card.TLabel", wraplength=295).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 5))
        self.output_entry = ttk.Entry(destination, textvariable=self.output_folder)
        self.output_entry.grid(row=2, column=0, sticky="ew")
        self.output_button = ttk.Button(destination, text="Browse...", command=self._choose_output)
        self.output_button.grid(row=2, column=1, padx=(6, 0))
        destination.columnconfigure(0, weight=1)

        ttk.Label(right, text="3  ·  WATERMARK STYLE", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        settings = ttk.Frame(right, style="Card.TFrame")
        settings.grid(row=1, column=0, sticky="nsew", pady=(10, 12))
        settings.columnconfigure(1, weight=1)
        ttk.Label(settings, text="Text", style="Card.TLabel").grid(row=0, column=0, sticky="w", pady=5)
        text_entry = ttk.Entry(settings, textvariable=self.text)
        text_entry.grid(row=0, column=1, columnspan=2, sticky="ew", pady=5)
        text_entry.bind("<KeyRelease>", lambda _event: self._draw_preview())
        ttk.Label(settings, text="Font", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=5)
        font_picker = ttk.Combobox(settings, textvariable=self.font_name, values=[name for name, _ in self.font_options], state="readonly")
        font_picker.grid(row=1, column=1, columnspan=2, sticky="ew", pady=5)
        font_picker.bind("<<ComboboxSelected>>", self._font_changed)
        ttk.Label(settings, text="Size", style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=5)
        font_slider = ttk.Scale(settings, from_=1, to=12, variable=self.font_scale, command=lambda _value: self._draw_preview())
        font_slider.grid(row=2, column=1, sticky="ew", pady=5)
        self.font_value = ttk.Label(settings, text="4.5 %", style="Card.TLabel", width=6)
        self.font_value.grid(row=2, column=2, sticky="e")
        font_slider.configure(command=self._font_size_changed)
        ttk.Label(settings, text="Opacity", style="Card.TLabel").grid(row=3, column=0, sticky="w", pady=5)
        opacity_slider = ttk.Scale(settings, from_=10, to=100, variable=self.opacity, command=self._opacity_changed)
        opacity_slider.grid(row=3, column=1, sticky="ew", pady=5)
        self.opacity_value = ttk.Label(settings, text="82 %", style="Card.TLabel", width=6)
        self.opacity_value.grid(row=3, column=2, sticky="e")

        colors = ttk.Frame(settings, style="Card.TFrame")
        colors.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(5, 6))
        ttk.Button(colors, text="Text color", command=self._choose_text_color).pack(side="left", padx=(0, 6))
        ttk.Button(colors, text="Watermark background", command=self._choose_background_color).pack(side="left")
        ttk.Label(settings, text="Logo (optional)", style="Card.TLabel").grid(row=5, column=0, sticky="w", pady=5)
        ttk.Entry(settings, textvariable=self.logo_path).grid(row=5, column=1, sticky="ew", pady=5)
        ttk.Button(settings, text="Browse...", command=self._choose_logo).grid(row=5, column=2, padx=(6, 0), pady=5)
        ttk.Label(settings, text="Drag the watermark on the preview to position it.", style="Card.TLabel", foreground="#667085").grid(row=6, column=0, columnspan=3, sticky="w", pady=(7, 0))

        ttk.Label(right, text="PREVIEW  ·  DRAG TO POSITION", style="Section.TLabel").grid(row=2, column=0, sticky="w", pady=(2, 8))
        self.canvas = tk.Canvas(right, bg="#e9edf5", highlightthickness=0, height=360)
        self.canvas.grid(row=3, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", lambda _event: self._draw_preview())
        self.canvas.bind("<ButtonPress-1>", self._start_drag)
        self.canvas.bind("<B1-Motion>", self._drag_watermark)
        self.canvas.bind("<ButtonRelease-1>", lambda _event: setattr(self, "dragging", False))

        footer = ttk.Frame(self.root, padding=(18, 0, 18, 14))
        footer.pack(fill="x")
        self.progress = ttk.Progressbar(footer, mode="determinate", maximum=100, style="Horizontal.TProgressbar")
        self.progress.pack(fill="x", pady=(0, 7))
        ttk.Label(footer, textvariable=self.status, foreground="#667085").pack(side="left")
        self.run_button = ttk.Button(footer, text="Run", style="Accent.TButton", command=self._run)
        self.run_button.pack(side="right")
        self._toggle_output()

    def _settings(self) -> WatermarkSettings:
        return WatermarkSettings(
            text=self.text.get(),
            text_color=self.text_color,
            background_color=self.background_color,
            opacity=round(self.opacity.get()),
            font_path=self.font_path.get() or None,
            font_scale=self.font_scale.get() / 100,
            logo_path=self.logo_path.get() or None,
            position_x=self.position_x,
            position_y=self.position_y,
        )

    def _choose_folder(self) -> None:
        chosen = filedialog.askdirectory(title="Select a photo folder")
        if not chosen:
            return
        folder = Path(chosen)
        files = collect_folder(folder)
        if not files:
            messagebox.showinfo("No photos found", "No supported photos were found in this folder.")
            return
        self.files = files
        self.source_root = folder
        self._refresh_files()
        self.status.set(f"Selected {len(files)} photo(s) from {folder}")
        self._draw_preview()

    def _choose_files(self) -> None:
        names = filedialog.askopenfilenames(
            title="Select photos",
            filetypes=[("Supported photos", "*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff")],
        )
        if not names:
            return
        files = sorted(set(self.files).union(Path(name) for name in names), key=lambda path: str(path).lower())
        try:
            source_root = Path(os.path.commonpath([str(path.parent) for path in files]))
        except ValueError:
            messagebox.showerror("Incompatible sources", "Photos must be on the same drive to preserve their folder structure.")
            return
        self.files = files
        self.source_root = source_root
        self._refresh_files()
        self.status.set(f"{len(self.files)} photo(s) selected")
        self._draw_preview()

    def _refresh_files(self) -> None:
        self.file_list.delete(0, tk.END)
        for path in self.files:
            self.file_list.insert(tk.END, f"{path.name}  ·  {path.parent}")
        if self.files:
            self.file_list.selection_set(0)
            self.file_list.activate(0)

    def _remove_selected(self) -> None:
        indexes = set(self.file_list.curselection())
        self.files = [path for index, path in enumerate(self.files) if index not in indexes]
        self._refresh_files()
        self._draw_preview()

    def _clear_files(self) -> None:
        self.files.clear()
        self.source_root = None
        self._refresh_files()
        self._draw_preview()
        self.status.set("No photos selected.")

    def _choose_output(self) -> None:
        chosen = filedialog.askdirectory(title="Choose an output folder")
        if chosen:
            self.output_folder.set(chosen)

    def _toggle_output(self) -> None:
        state = "disabled" if self.overwrite.get() else "normal"
        self.output_entry.configure(state=state)
        self.output_button.configure(state=state)

    def _choose_logo(self) -> None:
        chosen = filedialog.askopenfilename(title="Choose a logo", filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff"), ("All files", "*.*")])
        if chosen:
            self.logo_path.set(chosen)
            self._draw_preview()

    def _font_changed(self, _event: object) -> None:
        selected = self.font_name.get()
        self.font_path.set(next((path for name, path in self.font_options if name == selected), ""))
        self._draw_preview()

    def _font_size_changed(self, value: str) -> None:
        self.font_value.configure(text=f"{float(value):.1f} %")
        self._draw_preview()

    def _opacity_changed(self, value: str) -> None:
        self.opacity_value.configure(text=f"{round(float(value))} %")
        self._draw_preview()

    def _choose_text_color(self) -> None:
        chosen = colorchooser.askcolor(self.text_color, title="Text color")[1]
        if chosen:
            self.text_color = chosen
            self._draw_preview()

    def _choose_background_color(self) -> None:
        chosen = colorchooser.askcolor(self.background_color, title="Background color")[1]
        if chosen:
            self.background_color = chosen
            self._draw_preview()

    def _selected_preview_path(self) -> Path | None:
        selected = self.file_list.curselection()
        if selected:
            return self.files[selected[0]]
        return self.files[0] if self.files else None

    def _draw_preview(self) -> None:
        if not hasattr(self, "canvas"):
            return
        width, height = max(2, self.canvas.winfo_width()), max(2, self.canvas.winfo_height())
        self.canvas.delete("all")
        selected = self._selected_preview_path()
        preview_error = None
        if not selected:
            self.preview_image = None
            self.preview_source_path = None
        elif selected != self.preview_source_path:
            try:
                self.preview_image = create_preview(selected, (1600, 1000))
                self.preview_source_path = selected
            except (OSError, RuntimeError, ValueError) as exc:
                self.preview_image = None
                self.preview_source_path = None
                preview_error = str(exc)
                self.status.set(f"Preview unavailable: {exc}")
        if self.preview_image is None:
            self.preview_bounds = (0, 0, 0, 0)
            message = f"Preview unavailable\n{preview_error}" if preview_error else "Add photos\nto see a preview"
            self.canvas.create_text(width // 2, height // 2, text=message, fill="#667085", font=("Segoe UI", 10), justify="center", width=width - 40)
            return
        frame = self.preview_image.copy()
        frame.thumbnail((width - 20, height - 20), Image.Resampling.LANCZOS)
        if self.text.get().strip() or self.logo_path.get():
            try:
                watermark = render_overlay(frame.width, frame.height, self._settings())
                frame = Image.alpha_composite(frame.convert("RGBA"), watermark).convert("RGB")
            except (OSError, ValueError) as exc:
                self.status.set(f"Invalid watermark: {exc}")
        self.preview_photo = ImageTk.PhotoImage(frame)
        left = (width - frame.width) // 2
        top = (height - frame.height) // 2
        self.preview_bounds = (left, top, frame.width, frame.height)
        self.canvas.create_image(left, top, anchor="nw", image=self.preview_photo)
        self.font_value.configure(text=f"{self.font_scale.get():.1f} %")

    def _start_drag(self, event: tk.Event) -> None:
        self.dragging = True
        self._set_position(event.x, event.y)

    def _drag_watermark(self, event: tk.Event) -> None:
        if self.dragging:
            self._set_position(event.x, event.y)

    def _set_position(self, x: int, y: int) -> None:
        left, top, width, height = self.preview_bounds
        if width and height:
            self.position_x = max(0.0, min(1.0, (x - left) / width))
            self.position_y = max(0.0, min(1.0, (y - top) / height))
            self._draw_preview()

    def _run(self) -> None:
        if not self.files:
            messagebox.showwarning("No photos selected", "Select a folder or add photos first.")
            return
        if not self.text.get().strip() and not self.logo_path.get():
            messagebox.showwarning("Watermark is empty", "Enter text or choose a logo image.")
            return
        if self.logo_path.get() and not Path(self.logo_path.get()).is_file():
            messagebox.showerror("Logo not found", "The selected logo file no longer exists.")
            return
        if not self.overwrite.get():
            if not self.output_folder.get().strip():
                messagebox.showwarning("Output folder required", "Choose an output folder.")
                return
            output = Path(self.output_folder.get())
            if self.source_root and (output == self.source_root or self.source_root in output.parents):
                messagebox.showwarning("Invalid output folder", "Choose an output folder outside the source folder.")
                return
        if self.overwrite.get() and not messagebox.askyesno("Confirm overwrite", "Original photos will be replaced. This cannot be undone. Continue?"):
            return
        try:
            root = self.source_root or Path(os.path.commonpath([str(path.parent) for path in self.files]))
            if any(not path.is_relative_to(root) for path in self.files):
                root = Path(os.path.commonpath([str(path.parent) for path in self.files]))
        except ValueError:
            messagebox.showerror("Incompatible sources", "Selected photos must be on the same drive to preserve their folder structure.")
            return
        overwrite = self.overwrite.get()
        destination = root if overwrite else Path(self.output_folder.get())
        if not overwrite:
            conflicts = [path for path in self.files if (destination / path.relative_to(root)).exists()]
            if conflicts and not messagebox.askyesno(
                "Replace existing copies",
                f"{len(conflicts)} photo(s) already exist in the output folder and will be replaced. Continue?",
            ):
                return
        self.run_button.configure(state="disabled")
        self.progress.configure(value=0, maximum=len(self.files))
        self.status.set(f"Processing {len(self.files)} photo(s)…")
        worker = threading.Thread(target=self._process_worker, args=(root, destination, overwrite, self._settings()), daemon=True)
        worker.start()

    def _process_worker(self, root: Path, destination: Path, overwrite: bool, settings: WatermarkSettings) -> None:
        def update(index: int, total: int, source: Path, error: str | None) -> None:
            self.root.after(0, lambda: self._update_progress(index, total, source, error))

        succeeded, failures = process_batch(self.files.copy(), root, destination, overwrite, settings, update)
        self.root.after(0, lambda: self._finished(succeeded, failures))

    def _update_progress(self, index: int, total: int, source: Path, error: str | None) -> None:
        self.progress.configure(value=index, maximum=total)
        self.status.set(f"{index}/{total}  ·  {source.name}" + (f"  ·  Error: {error}" if error else ""))

    def _finished(self, succeeded: int, failures: list[tuple[Path, str]]) -> None:
        self.run_button.configure(state="normal")
        if failures:
            details = "\n".join(f"• {path.name}: {error[:180]}" for path, error in failures[:8])
            if len(failures) > 8:
                details += f"\n… and {len(failures) - 8} more error(s)."
            self.status.set(f"Done: {succeeded} succeeded, {len(failures)} failed.")
            messagebox.showwarning("Processing completed with errors", f"{succeeded} photo(s) processed, {len(failures)} failed.\n\n{details}")
        else:
            self.status.set(f"Done: {succeeded} photo(s) processed.")
            messagebox.showinfo("Processing complete", f"{succeeded} photo(s) processed successfully.")


def main() -> None:
    root = tk.Tk()
    AutoWatermarkApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
