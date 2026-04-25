# Copyright (C) 2026 Maurice
# This program is free software under the GNU GPL v3 license.
# See the LICENSE file for details.

import os
import json
import subprocess
import pyperclip

class ScriptsEngine:
    def __init__(self):
        self.config_path = os.path.join(os.path.dirname(__file__), "scripts.json")
        self.scripts = self.load_scripts()

    def load_scripts(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return [
            {"title": "Mise à jour Winget", "command": "winget upgrade --all", "mode": "PowerShell", "pause": True},
            {"title": "Lister IP", "command": "ipconfig /all", "mode": "PowerShell", "pause": True},
            {"title": "Copier Email", "command": "mon.email@exemple.com", "mode": "Copie", "pause": False}
        ]

    def save_scripts(self):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.scripts, f, indent=4, ensure_ascii=False)

    def run_script(self, script):
        cmd = script.get("command", "")
        mode = script.get("mode", "Hidden")
        pause = script.get("pause", False)

        try:
            if mode == "Hidden":
                subprocess.Popen(cmd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            elif mode == "PowerShell":
                if pause:
                    ps_cmd = f"{cmd}; Read-Host 'Pressez Entrée pour fermer...'"
                    full_cmd = f'powershell -NoExit -Command "{ps_cmd}"'
                else:
                    full_cmd = f'powershell -Command "{cmd}"'
                subprocess.Popen(f'start {full_cmd}', shell=True)
            elif mode == "Copie":
                pyperclip.copy(cmd)
        except Exception as e:
            return str(e)
        return None
