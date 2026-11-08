from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, Iterable, Optional

import imageio_ffmpeg
from PIL import Image

from watermark import WatermarkSettings, apply_to_image, render_overlay


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".mkv", ".avi"}
MEDIA_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS


def _temporary_path(destination: Path) -> Path:
    return destination.with_name(f".{destination.stem}.autowatermark-tmp{destination.suffix}")


def _extract_video_frame(source: Path) -> Image.Image:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    result = subprocess.run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            "00:00:00.1",
            "-i",
            str(source),
            "-frames:v",
            "1",
            "-f",
            "image2pipe",
            "-vcodec",
            "png",
            "pipe:1",
        ],
        capture_output=True,
        check=False,
        timeout=45,
    )
    if result.returncode or not result.stdout:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace").strip() or "Could not read a video frame.")
    from io import BytesIO

    return Image.open(BytesIO(result.stdout)).convert("RGBA")


def create_preview(source: Path, max_size: tuple[int, int] = (900, 520)) -> Image.Image:
    if source.suffix.lower() in IMAGE_EXTENSIONS:
        with Image.open(source) as image:
            from PIL import ImageOps

            preview = ImageOps.exif_transpose(image).convert("RGB")
    elif source.suffix.lower() in VIDEO_EXTENSIONS:
        preview = _extract_video_frame(source).convert("RGB")
    else:
        raise ValueError("The selected file type cannot be previewed.")
    preview.thumbnail(max_size, Image.Resampling.LANCZOS)
    return preview


def _process_video(source: Path, destination: Path, settings: WatermarkSettings) -> None:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    frame = _extract_video_frame(source)
    overlay = render_overlay(frame.width, frame.height, settings)
    temp_overlay = None
    temp_output = _temporary_path(destination)
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
            temp_overlay = Path(handle.name)
        overlay.save(temp_overlay)
        temp_output.parent.mkdir(parents=True, exist_ok=True)
        command = [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-loop",
            "1",
            "-framerate",
            "30",
            "-i",
            str(temp_overlay),
            "-filter_complex",
            "[0:v:0][1:v:0]overlay=0:0:format=auto",
            "-map",
            "0:v:0",
            "-map",
            "0:a?",
            "-map_metadata",
            "0",
            "-map_chapters",
            "0",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
        ]
        if destination.suffix.lower() in {".mp4", ".mov", ".m4v"}:
            command.extend(["-movflags", "+faststart"])
        command.append(str(temp_output))
        result = subprocess.run(command, capture_output=True, check=False)
        if result.returncode:
            message = result.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(message or "FFmpeg could not process this video.")
        os.replace(temp_output, destination)
    finally:
        if temp_overlay and temp_overlay.exists():
            temp_overlay.unlink()
        if temp_output.exists():
            temp_output.unlink()


def process_file(source: Path, destination: Path, settings: WatermarkSettings) -> None:
    extension = source.suffix.lower()
    if extension not in MEDIA_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {extension or '(no extension)'}")
    temp_output = _temporary_path(destination)
    try:
        if extension in IMAGE_EXTENSIONS:
            apply_to_image(source, temp_output, settings)
        else:
            _process_video(source, temp_output, settings)
        os.replace(temp_output, destination)
    finally:
        if temp_output.exists():
            temp_output.unlink()


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
        (path for path in folder.rglob("*") if path.is_file() and path.suffix.lower() in MEDIA_EXTENSIONS),
        key=lambda path: str(path).lower(),
    )
