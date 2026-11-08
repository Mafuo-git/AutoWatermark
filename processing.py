from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Iterable, Optional

from PIL import Image, ImageOps

from watermark import WatermarkSettings, apply_to_image, render_overlay


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


def create_preview(source: Path, max_size: tuple[int, int] = (900, 520)) -> Image.Image:
    if source.suffix.lower() not in IMAGE_EXTENSIONS:
        raise ValueError(f"Unsupported photo format: {source.suffix or '(no extension)'}")
    with Image.open(source) as image:
        preview = ImageOps.exif_transpose(image).convert("RGB")
    preview.thumbnail(max_size, Image.Resampling.LANCZOS)
    return preview


def process_file(source: Path, destination: Path, settings: WatermarkSettings) -> None:
    extension = source.suffix.lower()
    if extension not in IMAGE_EXTENSIONS:
        raise ValueError(f"Unsupported photo format: {extension or '(no extension)'}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.stem}.autowatermark-tmp{destination.suffix}")
    try:
        apply_to_image(source, temporary, settings)
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def process_batch(
    files: Iterable[Path],
    source_root: Path,
    output_root: Path,
    overwrite: bool,
    settings: WatermarkSettings,
    progress: Optional[Callable[[int, int, Path, Optional[str]], None]] = None,
) -> tuple[int, list[tuple[Path, str]]]:
    items = list(files)
    failures: list[tuple[Path, str]] = []
    succeeded = 0
    for index, source in enumerate(items, start=1):
        destination = source if overwrite else output_root / source.relative_to(source_root)
        try:
            process_file(source, destination, settings)
            succeeded += 1
            error = None
        except Exception as exc:
            error = str(exc)
            failures.append((source, error))
        if progress:
            progress(index, len(items), source, error)
    return succeeded, failures


def collect_folder(folder: Path) -> list[Path]:
    return sorted(
        (path for path in folder.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS),
        key=lambda path: str(path).lower(),
    )
