# Copyright (C) 2026 Maurice
# This program is free software under the GNU GPL v3 license.
# See the LICENSE file for details.

from utils import run_command

class RepairToolsEngine:
    def run_sfc(self, log_cb):
        log_cb("Lancement de SFC (System File Checker)...")
        success, out, _ = run_command("sfc /scannow")
        log_cb(out)
        return success

    def run_dism(self, log_cb):
        log_cb("Lancement de DISM (RestoreHealth)...")
        success, out, _ = run_command("DISM /Online /Cleanup-Image /RestoreHealth")
        log_cb(out)
        return success
