@echo off
echo Construction de l'executable DiagPcNet...
pyinstaller --noconfirm --onefile --windowed --add-data "coffee.md;." --add-data "QR_BTC.jpg;." --add-data "assets;assets" --name "DiagPcNet" main.py
pause
