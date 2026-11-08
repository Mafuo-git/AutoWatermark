from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont


@dataclass
class WatermarkSettings:
    text: str = "© Your Name"
    text_color: str = "#FFFFFF"
    background_color: Optional[str] = "#000000"
    opacity: int = 72
    font_path: Optional[str] = None
    font_scale: float = 0.045
    logo_path: Optional[str] = None
    logo_scale: float = 0.18
    position_x: float = 0.94
    position_y: float = 0.94


def available_fonts() -> list[tuple[str, str]]:
    fonts_dir = Path("C:/Windows/Fonts")
    if not fonts_dir.is_dir():
        return [("Arial", "C:/Windows/Fonts/arial.ttf")]
    fonts = []
    for path in sorted(fonts_dir.glob("*.ttf")):
        fonts.append((path.stem, str(path)))
    for path in sorted(fonts_dir.glob("*.otf")):
        fonts.append((path.stem, str(path)))
    return fonts or [("Arial", "C:/Windows/Fonts/arial.ttf")]


def _font(settings: WatermarkSettings, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if settings.font_path and Path(settings.font_path).is_file():
        return ImageFont.truetype(settings.font_path, size=size)
    try:
        return ImageFont.truetype("arial.ttf", size=size)
    except OSError:
        return ImageFont.load_default()


def _with_alpha(color: str, opacity: int) -> tuple[int, int, int, int]:
    rgb = Image.new("RGB", (1, 1), color).getpixel((0, 0))
    return rgb[0], rgb[1], rgb[2], max(0, min(255, round(opacity * 255 / 100)))


def render_overlay(width: int, height: int, settings: WatermarkSettings) -> Image.Image:
    """Render a full-frame transparent watermark overlay."""
    if width < 1 or height < 1:
        raise ValueError("The image dimensions must be positive.")
    if not settings.text.strip() and not settings.logo_path:
        raise ValueError("Enter watermark text or choose a logo.")

    opacity = max(0, min(100, settings.opacity))
    font_size = max(10, round(height * max(0.005, min(settings.font_scale, 0.25))))
    font = _font(settings, font_size)
    padding = max(2, round(min(width, height) * 0.012))
    logo = None
    if settings.logo_path:
        with Image.open(settings.logo_path) as source_logo:
            logo = source_logo.convert("RGBA")
        max_logo_width = max(1, round(width * max(0.02, min(settings.logo_scale, 0.8))))
        max_logo_height = max(1, round(height * 0.3))
        logo.thumbnail((max_logo_width, max_logo_height), Image.Resampling.LANCZOS)
        alpha = logo.getchannel("A").point(lambda value: round(value * opacity / 100))
        logo.putalpha(alpha)

    probe = Image.new("RGBA", (1, 1))
    draw = ImageDraw.Draw(probe)
    text_box = draw.multiline_textbbox((0, 0), settings.text, font=font, spacing=max(2, font_size // 5)) if settings.text.strip() else None
    text_width = text_box[2] - text_box[0] if text_box else 0
    text_height = text_box[3] - text_box[1] if text_box else 0
    gap = padding if logo and text_width else 0
    content_width = max(text_width, logo.width if logo else 0)
    content_height = text_height + (logo.height + gap if logo else 0)
    box_width = min(width, content_width + padding * 2)
    box_height = min(height, content_height + padding * 2)

    center_x = round(max(0.0, min(1.0, settings.position_x)) * width)
    center_y = round(max(0.0, min(1.0, settings.position_y)) * height)
    left = max(0, min(width - box_width, center_x - box_width // 2))
    top = max(0, min(height - box_height, center_y - box_height // 2))

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    box = Image.new("RGBA", (box_width, box_height), (0, 0, 0, 0))
    box_draw = ImageDraw.Draw(box)
    if settings.background_color:
        box_draw.rounded_rectangle(
            (0, 0, box_width - 1, box_height - 1),
            radius=max(2, padding // 2),
            fill=_with_alpha(settings.background_color, opacity),
        )

    cursor_y = padding
    if logo:
        logo_x = (box_width - logo.width) // 2
        box.alpha_composite(logo, (logo_x, cursor_y))
        cursor_y += logo.height + gap
    if text_box:
        text_x = (box_width - text_width) // 2 - text_box[0]
        text_y = cursor_y - text_box[1]
        box_draw.multiline_text(
            (text_x, text_y),
            settings.text,
            font=font,
            fill=_with_alpha(settings.text_color, opacity),
            spacing=max(2, font_size // 5),
        )
    overlay.alpha_composite(box, (left, top))
    return overlay


def apply_to_image(source: Path, destination: Path, settings: WatermarkSettings) -> None:
    with Image.open(source) as original:
        from PIL import ImageOps

        corrected = ImageOps.exif_transpose(original).convert("RGBA")
        overlay = render_overlay(corrected.width, corrected.height, settings)
        result = Image.alpha_composite(corrected, overlay)
        destination.parent.mkdir(parents=True, exist_ok=True)
        suffix = destination.suffix.lower()
        save_options: dict[str, object] = {}
        exif = original.getexif()
        if exif and suffix != ".bmp":
            exif[274] = 1
            save_options["exif"] = exif.tobytes()
        if original.info.get("icc_profile") and suffix != ".bmp":
            save_options["icc_profile"] = original.info["icc_profile"]
        if suffix in {".jpg", ".jpeg"}:
            result.convert("RGB").save(destination, quality=95, optimize=True, **save_options)
        elif suffix == ".bmp":
            result.convert("RGB").save(destination, **save_options)
        elif suffix == ".gif":
            result.convert("RGB").save(destination, **save_options)
        else:
            result.save(destination, **save_options)
