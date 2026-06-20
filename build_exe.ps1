$ErrorActionPreference = "Stop"

python -m pip install --upgrade pyinstaller
python -m PyInstaller `
  --noconfirm `
  --clean `
  --onefile `
  --windowed `
  --name "Wrasul-LOL-Item-Build-Importer" `
  --paths "src" `
  "scripts\gui_launcher.py"

Write-Host "Built: dist\Wrasul-LOL-Item-Build-Importer.exe"
