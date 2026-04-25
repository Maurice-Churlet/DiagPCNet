# Copyright (C) 2026 Maurice
# This program is free software under the GNU GPL v3 license.
# See the LICENSE file for details.

import os
import winreg
from utils import run_command, logger

class ManagerEngine:
    def get_startup_items(self):
        """Liste les programmes au démarrage (HKCU and HKLM)."""
        items = []
        keys = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run")
        ]
        
        for root, path in keys:
            try:
                key = winreg.OpenKey(root, path)
                for i in range(winreg.QueryInfoKey(key)[1]):
                    name, val, _ = winreg.EnumValue(key, i)
                    items.append({"name": name, "path": val, "location": "Registry"})
                winreg.CloseKey(key)
            except:
                pass
        return items

    def get_installed_software(self):
        """Liste les logiciels installés (via registre)."""
        software = []
        path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
        
        # Check both 32-bit and 64-bit registry
        for root in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
            for access in [winreg.KEY_READ | winreg.KEY_WOW64_64KEY, winreg.KEY_READ | winreg.KEY_WOW64_32KEY]:
                try:
                    key = winreg.OpenKey(root, path, 0, access)
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        sub_key_name = winreg.EnumKey(key, i)
                        try:
                            sub_key = winreg.OpenKey(key, sub_key_name)
                            name, _ = winreg.QueryValueEx(sub_key, "DisplayName")
                            try: version, _ = winreg.QueryValueEx(sub_key, "DisplayVersion")
                            except: version = "Inconnue"
                            software.append({"name": name, "version": version})
                            winreg.CloseKey(sub_key)
                        except:
                            pass
                    winreg.CloseKey(key)
                except:
                    pass
        return sorted(software, key=lambda x: x["name"])
