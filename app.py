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
        self.status = tk.StringVar(value="Ajoutez des fichiers ou sélectionnez un dossier pour commencer.")
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
        ttk.Label(header, text="Filigranez vos photos et vidéos, en toute simplicité", foreground="#667085").pack(side="left", padx=14, pady=(5, 0))
        ttk.Label(header, text="Windows · traitement local", foreground="#667085").pack(side="right", pady=(5, 0))

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

        ttk.Label(left, text="1  ·  FICHIERS SOURCE", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        source_actions = ttk.Frame(left, style="Card.TFrame")
        source_actions.grid(row=1, column=0, sticky="ew", pady=(8, 6))
        ttk.Button(source_actions, text="Choisir un dossier", command=self._choose_folder).pack(side="left", padx=(0, 6))
        ttk.Button(source_actions, text="Ajouter des fichiers", command=self._choose_files).pack(side="left")
        self.file_list = tk.Listbox(left, height=8, selectmode=tk.EXTENDED, relief="flat", borderwidth=0, highlightthickness=1, highlightbackground="#dce2ed", font=("Segoe UI", 9), activestyle="none")
        self.file_list.grid(row=2, column=0, sticky="nsew")
        self.file_list.bind("<<ListboxSelect>>", lambda _event: self._draw_preview())
        file_buttons = ttk.Frame(left, style="Card.TFrame")
        file_buttons.grid(row=3, column=0, sticky="ew", pady=(5, 12))
        ttk.Button(file_buttons, text="Retirer la sélection", command=self._remove_selected).pack(side="left")
        ttk.Button(file_buttons, text="Tout effacer", command=self._clear_files).pack(side="left", padx=6)

        ttk.Label(left, text="2  ·  SORTIE", style="Section.TLabel").grid(row=4, column=0, sticky="nw", pady=(0, 7))
        destination = ttk.Frame(left, style="Card.TFrame")
        destination.grid(row=5, column=0, sticky="ew")
        ttk.Checkbutton(destination, text="Remplacer les fichiers originaux", variable=self.overwrite, command=self._toggle_output).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 7))
        ttk.Label(destination, text="Sinon, enregistrez une copie dans un dossier de sortie :", style="Card.TLabel", wraplength=295).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 5))
        self.output_entry = ttk.Entry(destination, textvariable=self.output_folder)
        self.output_entry.grid(row=2, column=0, sticky="ew")
        self.output_button = ttk.Button(destination, text="Parcourir…", command=self._choose_output)
        self.output_button.grid(row=2, column=1, padx=(6, 0))
        destination.columnconfigure(0, weight=1)

        ttk.Label(right, text="3  ·  APPARENCE DU FILIGRANE", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        settings = ttk.Frame(right, style="Card.TFrame")
        settings.grid(row=1, column=0, sticky="nsew", pady=(10, 12))
        settings.columnconfigure(1, weight=1)
        ttk.Label(settings, text="Texte", style="Card.TLabel").grid(row=0, column=0, sticky="w", pady=5)
        text_entry = ttk.Entry(settings, textvariable=self.text)
        text_entry.grid(row=0, column=1, columnspan=2, sticky="ew", pady=5)
        text_entry.bind("<KeyRelease>", lambda _event: self._draw_preview())
        ttk.Label(settings, text="Police", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=5)
        font_picker = ttk.Combobox(settings, textvariable=self.font_name, values=[name for name, _ in self.font_options], state="readonly")
        font_picker.grid(row=1, column=1, columnspan=2, sticky="ew", pady=5)
        font_picker.bind("<<ComboboxSelected>>", self._font_changed)
        ttk.Label(settings, text="Taille", style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=5)
        font_slider = ttk.Scale(settings, from_=1, to=12, variable=self.font_scale, command=lambda _value: self._draw_preview())
        font_slider.grid(row=2, column=1, sticky="ew", pady=5)
        self.font_value = ttk.Label(settings, text="4.5 %", style="Card.TLabel", width=6)
        self.font_value.grid(row=2, column=2, sticky="e")
        font_slider.configure(command=self._font_size_changed)
        ttk.Label(settings, text="Opacité", style="Card.TLabel").grid(row=3, column=0, sticky="w", pady=5)
        opacity_slider = ttk.Scale(settings, from_=10, to=100, variable=self.opacity, command=self._opacity_changed)
        opacity_slider.grid(row=3, column=1, sticky="ew", pady=5)
        self.opacity_value = ttk.Label(settings, text="82 %", style="Card.TLabel", width=6)
        self.opacity_value.grid(row=3, column=2, sticky="e")

        colors = ttk.Frame(settings, style="Card.TFrame")
        colors.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(5, 6))
        ttk.Button(colors, text="Couleur du texte", command=self._choose_text_color).pack(side="left", padx=(0, 6))
        ttk.Button(colors, text="Fond du filigrane", command=self._choose_background_color).pack(side="left")
        ttk.Label(settings, text="Logo (facultatif)", style="Card.TLabel").grid(row=5, column=0, sticky="w", pady=5)
        ttk.Entry(settings, textvariable=self.logo_path).grid(row=5, column=1, sticky="ew", pady=5)
        ttk.Button(settings, text="Parcourir…", command=self._choose_logo).grid(row=5, column=2, padx=(6, 0), pady=5)
        ttk.Label(settings, text="Faites glisser le filigrane sur l’aperçu pour le déplacer.", style="Card.TLabel", foreground="#667085").grid(row=6, column=0, columnspan=3, sticky="w", pady=(7, 0))

        ttk.Label(right, text="APERÇU  ·  GLISSER-DÉPOSER POUR POSITIONNER", style="Section.TLabel").grid(row=2, column=0, sticky="w", pady=(2, 8))
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
        self.run_button = ttk.Button(footer, text="Exécuter", style="Accent.TButton", command=self._run)
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
        chosen = filedialog.askdirectory(title="Sélectionner un dossier de photos et vidéos")
        if not chosen:
            return
        folder = Path(chosen)
        files = collect_folder(folder)
        if not files:
            messagebox.showinfo("Aucun média", "Aucune photo ou vidéo prise en charge n’a été trouvée dans ce dossier.")
            return
        self.files = files
        self.source_root = folder
        self._refresh_files()
        self.status.set(f"{len(files)} fichier(s) sélectionné(s) dans {folder}")
        self._draw_preview()

    def _choose_files(self) -> None:
        names = filedialog.askopenfilenames(
            title="Sélectionner des photos et vidéos",
            filetypes=[("Photos et vidéos prises en charge", "*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff *.mp4 *.mov *.m4v *.mkv *.avi"), ("Tous les fichiers", "*.*")],
        )
        if not names:
            return
        files = sorted(set(self.files).union(Path(name) for name in names), key=lambda path: str(path).lower())
        try:
            source_root = Path(os.path.commonpath([str(path.parent) for path in files]))
        except ValueError:
            messagebox.showerror("Sources incompatibles", "Les fichiers doivent se trouver sur le même lecteur pour préserver leur arborescence.")
            return
        self.files = files
        self.source_root = source_root
        self._refresh_files()
        self.status.set(f"{len(self.files)} fichier(s) sélectionné(s)")
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
        self.status.set("Aucun fichier sélectionné.")

    def _choose_output(self) -> None:
        chosen = filedialog.askdirectory(title="Choisir le dossier de sortie")
        if chosen:
            self.output_folder.set(chosen)

    def _toggle_output(self) -> None:
        state = "disabled" if self.overwrite.get() else "normal"
        self.output_entry.configure(state=state)
        self.output_button.configure(state=state)

    def _choose_logo(self) -> None:
        chosen = filedialog.askopenfilename(title="Choisir un logo", filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff"), ("Tous les fichiers", "*.*")])
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
        chosen = colorchooser.askcolor(self.text_color, title="Couleur du texte")[1]
        if chosen:
            self.text_color = chosen
            self._draw_preview()

    def _choose_background_color(self) -> None:
        chosen = colorchooser.askcolor(self.background_color, title="Couleur du fond")[1]
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
                self.status.set(f"Aperçu indisponible : {exc}")
        if self.preview_image is None:
            self.preview_bounds = (0, 0, 0, 0)
            message = f"Aperçu indisponible\n{preview_error}" if preview_error else "Ajoutez des photos ou vidéos\npour afficher un aperçu"
            self.canvas.create_text(width // 2, height // 2, text=message, fill="#667085", font=("Segoe UI", 10), justify="center", width=width - 40)
            return
        frame = self.preview_image.copy()
        frame.thumbnail((width - 20, height - 20), Image.Resampling.LANCZOS)
        if self.text.get().strip() or self.logo_path.get():
            try:
                watermark = render_overlay(frame.width, frame.height, self._settings())
                frame = Image.alpha_composite(frame.convert("RGBA"), watermark).convert("RGB")
            except (OSError, ValueError) as exc:
                self.status.set(f"Filigrane invalide : {exc}")
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
            messagebox.showwarning("Aucun fichier", "Sélectionnez d’abord un dossier ou des fichiers.")
            return
        if not self.text.get().strip() and not self.logo_path.get():
            messagebox.showwarning("Filigrane manquant", "Ajoutez du texte ou sélectionnez une image de logo.")
            return
        if self.logo_path.get() and not Path(self.logo_path.get()).is_file():
            messagebox.showerror("Logo introuvable", "Le fichier du logo sélectionné n’existe plus.")
            return
        if not self.overwrite.get():
            if not self.output_folder.get().strip():
                messagebox.showwarning("Dossier de sortie manquant", "Choisissez un dossier de sortie.")
                return
            output = Path(self.output_folder.get())
            if self.source_root and (output == self.source_root or self.source_root in output.parents):
                messagebox.showwarning("Dossier de sortie invalide", "Choisissez un dossier de sortie en dehors du dossier source.")
                return
        if self.overwrite.get() and not messagebox.askyesno("Confirmer le remplacement", "Les fichiers originaux seront remplacés. Cette action est irréversible. Continuer ?"):
            return
        try:
            root = self.source_root or Path(os.path.commonpath([str(path.parent) for path in self.files]))
            if any(not path.is_relative_to(root) for path in self.files):
                root = Path(os.path.commonpath([str(path.parent) for path in self.files]))
        except ValueError:
            messagebox.showerror("Sources incompatibles", "Les fichiers sélectionnés doivent se trouver sur le même lecteur pour préserver leur arborescence.")
            return
        overwrite = self.overwrite.get()
        destination = root if overwrite else Path(self.output_folder.get())
        if not overwrite:
            conflicts = [path for path in self.files if (destination / path.relative_to(root)).exists()]
            if conflicts and not messagebox.askyesno(
                "Remplacer les copies existantes",
                f"{len(conflicts)} fichier(s) existent déjà dans le dossier de sortie et seront remplacés. Continuer ?",
            ):
                return
        self.run_button.configure(state="disabled")
        self.progress.configure(value=0, maximum=len(self.files))
        self.status.set(f"Traitement de {len(self.files)} fichier(s)…")
        worker = threading.Thread(target=self._process_worker, args=(root, destination, overwrite, self._settings()), daemon=True)
        worker.start()

    def _process_worker(self, root: Path, destination: Path, overwrite: bool, settings: WatermarkSettings) -> None:
        def update(index: int, total: int, source: Path, error: str | None) -> None:
            self.root.after(0, lambda: self._update_progress(index, total, source, error))

        succeeded, failures = process_batch(self.files.copy(), root, destination, overwrite, settings, update)
        self.root.after(0, lambda: self._finished(succeeded, failures))

    def _update_progress(self, index: int, total: int, source: Path, error: str | None) -> None:
        self.progress.configure(value=index, maximum=total)
        self.status.set(f"{index}/{total}  ·  {source.name}" + (f"  ·  Erreur : {error}" if error else ""))

    def _finished(self, succeeded: int, failures: list[tuple[Path, str]]) -> None:
        self.run_button.configure(state="normal")
        if failures:
            details = "\n".join(f"• {path.name} : {error[:180]}" for path, error in failures[:8])
            if len(failures) > 8:
                details += f"\n… et {len(failures) - 8} autre(s) erreur(s)."
            self.status.set(f"Terminé : {succeeded} réussi(s), {len(failures)} erreur(s).")
            messagebox.showwarning("Traitement terminé avec des erreurs", f"{succeeded} fichier(s) traité(s), {len(failures)} en erreur.\n\n{details}")
        else:
            self.status.set(f"Terminé : {succeeded} fichier(s) traité(s).")
            messagebox.showinfo("Traitement terminé", f"{succeeded} fichier(s) traité(s) avec succès.")


def main() -> None:
    root = tk.Tk()
    AutoWatermarkApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
