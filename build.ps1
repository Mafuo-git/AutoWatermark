$ErrorActionPreference = "Stop"

python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }

python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw "The test suite failed." }

python -m PyInstaller --noconfirm --clean --onefile --windowed --name AutoWatermark app.py
if ($LASTEXITCODE -ne 0) { throw "The executable build failed." }

Write-Host ""
Write-Host "Portable executable created at: dist\AutoWatermark.exe"
