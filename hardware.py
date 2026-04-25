# Copyright (C) 2026 Maurice
# This program is free software under the GNU GPL v3 license.
# See the LICENSE file for details.

from utils import run_command, logger

class HardwareEngine:
    def audit_system(self):
        """Réalise un audit complet des composants clés."""
        audit = {}
        
        # CPU
        success, out, _ = run_command("wmic cpu get name, MaxClockSpeed, NumberOfCores")
        audit["CPU"] = out.strip().splitlines()[-1] if success else "Inconnu"
        
        # RAM
        success, out, _ = run_command("wmic ComputerSystem get TotalPhysicalMemory")
        if success:
            bytes_val = out.strip().splitlines()[-1]
            if bytes_val.isdigit():
                audit["RAM"] = f"{int(bytes_val) // (1024**3)} GB"
        
        # GPU
        success, out, _ = run_command("wmic path win32_VideoController get name")
        audit["GPU"] = out.strip().splitlines()[-1] if success else "Inconnu"
        
        # Disques Physiques
        success, out, _ = run_command("powershell -Command \"Get-PhysicalDisk | Select-Object FriendlyName, MediaType, Size\"")
        audit["Disques"] = out.strip() if success else "Inconnu"
        
        # OS Info
        success, out, _ = run_command("wmic os get Caption, Version, OSArchitecture")
        audit["OS"] = out.strip().splitlines()[-1] if success else "Inconnu"

        return audit

    def check_battery(self):
        """Vérifie l'état de la batterie."""
        ps_cmd = "Get-CimInstance -ClassName Win32_Battery | Select-Object EstimatedChargeRemaining, BatteryStatus"
        success, out, _ = run_command(f"powershell -Command \"{ps_cmd}\"")
        if not out.strip(): return "Aucune batterie détectée (PC Fixe?)"
        return out.strip()

    def check_windows_updates(self):
        """Vérifie s'il y a des mises à jour en attente (rapide)."""
        ps_cmd = "$updateSession = New-Object -ComObject 'Microsoft.Update.Session'; $updateSearcher = $updateSession.CreateUpdateSearcher(); $searchResult = $updateSearcher.Search('IsInstalled=0 and DeploymentAction=*'); $searchResult.Updates.Count"
        success, out, _ = run_command(f"powershell -Command \"{ps_cmd}\"")
        if success and out.strip().isdigit():
            count = int(out.strip())
            return f"{count} mise(s) à jour en attente."
        return "Impossible de vérifier les mises à jour."

    def list_usb_devices(self):
        """Liste les périphériques USB connectés."""
        ps_cmd = "Get-PnpDevice -PresentOnly | Where-Object { $_.InstanceId -match 'USB' } | Select-Object FriendlyName, Status, Class"
        success, out, err = run_command(f"powershell -Command \"{ps_cmd}\"")
        return out.strip() if success else "Erreur de lecture USB"

    def check_drivers_health(self):
        """Vérifie si des pilotes posent problème."""
        ps_cmd = "Get-PnpDevice | Where-Object { $_.Status -ne 'OK' } | Select-Object FriendlyName, Problem, Status"
        success, out, err = run_command(f"powershell -Command \"{ps_cmd}\"")
        return out.strip() if success else "Tous les pilotes sont OK"
