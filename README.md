<div align="center">

# AutoWatermark

### A simple, offline tool for watermarking photos and videos in bulk.

Choose your media, style a text-and-logo watermark, drag it into place, and export.

![Windows](https://img.shields.io/badge/platform-Windows-0078D4?logo=windows&logoColor=white)
![Standalone](https://img.shields.io/badge/download-single%20portable%20EXE-3157D5)
![License](https://img.shields.io/badge/license-MIT-2E8B57)

</div>

---

### The workflow

`📁 Select media` **→** `🎨 Style your watermark` **→** `↔ Drag to position` **→** `✨ Export`

| 🖼️ Customize | 🎬 Process | 🛡️ Stay in control |
|:---|:---|:---|
| Text, logo, font, colors, size and opacity | Photos and videos, individually or by folder | Preview before processing; preserve originals by default |
| Position your watermark directly on the preview | Folder selection includes subfolders | Optional overwrite requires confirmation |

## Get the Windows app

Download **AutoWatermark-Windows-x64** from the latest successful run of [Build Windows executable](../../actions/workflows/build-windows.yml), then extract and double-click `AutoWatermark.exe`.

The app is distributed as a single, self-contained Windows executable. The target PC does not need Python, FFmpeg, or separately installed libraries. The first launch may take a little longer while Windows scans the unsigned executable.

## Use it

1. Select a folder or add individual media files.
2. Choose a separate output folder (recommended).
3. Set your text, font, colors, opacity, and optional logo.
4. Drag the watermark on the preview to position it.
5. Click **Run** and check the completion report.

> **Protect your originals:** Output to a separate folder by default. Overwriting is optional, requires confirmation, and cannot be undone.

### Supported formats

| Photos and logos | Videos |
|:---|:---|
| JPEG · PNG · WebP · BMP · TIFF | MP4 · MOV · M4V · MKV · AVI |

Videos are re-encoded as H.264 with AAC audio. Processing time and output characteristics depend on the source video. Unsupported or unreadable files are reported; failed jobs leave their originals intact.

## Build from source

On Windows, install Python 3.12, then run in PowerShell:

```powershell
.\build.ps1
```

The script installs dependencies, runs the test suite, and builds `dist\AutoWatermark.exe`.

For development:

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python app.py
```

## Privacy and licenses

Media is processed locally and is not uploaded. The MIT-licensed project uses [Pillow](https://python-pillow.org/), [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg), and [PyInstaller](https://pyinstaller.org/). Bundled FFmpeg and other third-party components are subject to their own licenses; see [LICENSE](./LICENSE).
