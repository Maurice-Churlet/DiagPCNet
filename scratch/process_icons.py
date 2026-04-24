# Copyright (C) 2026 Maurice
# This program is free software under the GNU GPL v3 license.
# See the LICENSE file for details.

from PIL import Image
import os

# Paths
logo_3d = r"C:\Users\mchur\.gemini\antigravity\brain\e58f6842-0098-40c2-ab91-edfb72153974\diagpcnet_logo_concept_1777043323300.png"
icon_flat = r"C:\Users\mchur\.gemini\antigravity\brain\e58f6842-0098-40c2-ab91-edfb72153974\diagpcnet_icon_flat_1777043348826.png"
assets_dir = r"c:\Dev\DiagPcNet\assets"

# 1. Save 3D Logo as assets/logo.png (512x512)
img_logo = Image.open(logo_3d)
img_logo = img_logo.resize((512, 512), Image.LANCZOS)
img_logo.save(os.path.join(assets_dir, "logo.png"))
print("Saved assets/logo.png")

# 2. Save Flat Icon as assets/icon.png (256x256)
img_icon = Image.open(icon_flat)
img_icon = img_icon.resize((256, 256), Image.LANCZOS)
img_icon.save(os.path.join(assets_dir, "icon.png"))
print("Saved assets/icon.png")

# 3. Save as .ico (multi-resolution)
img_icon.save(os.path.join(assets_dir, "icon.ico"), format='ICO', sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])
print("Saved assets/icon.ico")
