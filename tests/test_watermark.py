import tempfile
import unittest
from pathlib import Path

from PIL import Image

from processing import collect_folder, create_preview, process_file
from watermark import WatermarkSettings, render_overlay


class WatermarkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = WatermarkSettings(
            text="Copyright",
            text_color="#FFFFFF",
            background_color="#000000",
            opacity=100,
            font_scale=0.1,
            position_x=0.5,
            position_y=0.5,
        )

    def test_overlay_has_transparent_background_and_visible_label(self) -> None:
        overlay = render_overlay(400, 200, self.settings)
        self.assertEqual(overlay.size, (400, 200))
        self.assertEqual(overlay.getpixel((0, 0))[3], 0)
        self.assertIsNotNone(overlay.getchannel("A").getbbox())

    def test_overlay_position_is_clamped_to_frame(self) -> None:
        settings = WatermarkSettings(text="Label", opacity=100, position_x=8, position_y=-3)
        overlay = render_overlay(160, 90, settings)
        self.assertEqual(overlay.size, (160, 90))
        self.assertIsNotNone(overlay.getchannel("A").getbbox())

    def test_create_preview_loads_and_scales_photo(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "photo.png"
            Image.new("RGB", (160, 120), "#3a7d44").save(source)

            preview = create_preview(source, (80, 60))

            self.assertEqual(preview.size, (80, 60))

    def test_process_file_creates_watermarked_image(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "photo.png"
            destination = Path(temporary_directory) / "output" / "photo.png"
            Image.new("RGB", (240, 120), "#3a7d44").save(source)

            process_file(source, destination, self.settings)

            with Image.open(destination) as result:
                self.assertEqual(result.size, (240, 120))
                self.assertNotEqual(result.getpixel((120, 60)), (58, 125, 68, 255))

    def test_process_file_rejects_video(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "clip.mp4"
            destination = Path(temporary_directory) / "output" / "clip.mp4"
            with self.assertRaisesRegex(ValueError, "Unsupported photo format"):
                process_file(source, destination, self.settings)
            self.assertFalse(destination.exists())

    def test_collect_folder_ignores_videos(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            folder = Path(temporary_directory)
            photo = folder / "photo.jpg"
            video = folder / "clip.mp4"
            photo.touch()
            video.touch()

            self.assertEqual(collect_folder(folder), [photo])


if __name__ == "__main__":
    unittest.main()
