# Copyright (C) 2026 Maurice
# This program is free software under the GNU GPL v3 license.
# See the LICENSE file for details.

import winreg
from utils import run_command, logger

class DiagnosticEngine:
    def __init__(self):
        self.results = []
        self.severity = "OK"

    def add_result(self, category, name, status, message, severity="OK"):
        self.results.append({
            "category": category,
            "name": name,
            "status": status,
            "message": message,
            "severity": severity
        })
        if severity == "CRITICAL":
            self.severity = "CRITICAL"
        elif severity == "WARNING" and self.severity != "CRITICAL":
            self.severity = "WARNING"

    def run_all(self):
        self.results = []
        self.severity = "OK"
        
        logger.info("Démarrage du diagnostic complet...")
        self.check_network()
        self.check_services()
        self.check_smb_share()
        self.check_firewall()
        self.check_registry()
        self.check_event_viewer()
        logger.info(f"Diagnostic terminé. Statut global: {self.severity}")
        
        return self.results, self.severity

    def check_network(self):
        success, out, err = run_command("ipconfig /all")
        self.add_result("Réseau", "IPConfig", "OK" if success else "ERR", "Configuration IP récupérée")
        
        ps_cmd = "Get-NetConnectionProfile | Select-Object -ExpandProperty NetworkCategory"
        success, out, err = run_command(f"powershell -Command \"{ps_cmd}\"")
        is_private = "Private" in out or "Domain" in out
        self.add_result("Réseau", "Profil", "OK" if is_private else "WARN", 
                        f"Profil actuel: {out.strip()}", "OK" if is_private else "WARNING")

    def check_services(self):
        services = ["fdPHost", "FDResPub", "SSDPSRV", "upnphost", "LanmanWorkstation", "LanmanServer"]
        for svc in services:
            success, out, err = run_command(f"sc query {svc}")
            running = "RUNNING" in out
            
            success_start, out_start, _ = run_command(f"sc qc {svc}")
            auto = "AUTO_START" in out_start or "DEMAND_START" in out_start # Demand is acceptable for some
            
            status = "OK" if running else "WARN"
            msg = f"Etat: {'En cours' if running else 'Arrêté'}, Démarrage: {'Auto' if 'AUTO' in out_start else 'Manuel/Désactivé'}"
            self.add_result("Service", svc, status, msg, "OK" if running else "WARNING")

    def check_smb_share(self):
        success, out, err = run_command("net share")
        self.add_result("SMB", "Partages", "OK" if success else "ERR", "Liste des partages récupérée")
        
        success, out, err = run_command("net view \\\\localhost")
        self.add_result("SMB", "Visibilité", "OK" if success else "WARN", 
                        "localhost accessible" if success else "localhost non listé (net view)",
                        "OK" if success else "WARNING")

    def check_firewall(self):
        cmd = "netsh advfirewall show allprofiles state"
        success, out, err = run_command(cmd)
        self.add_result("Firewall", "État", "OK", "Analyse effectuée")

    def check_registry(self):
        try:
            key_path = r"SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters"
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
            try:
                val, _ = winreg.QueryValueEx(key, "AllowInsecureGuestAuth")
                status = "OK" if val == 1 else "WARN"
                msg = f"AllowInsecureGuestAuth: {val}"
                self.add_result("Registre", "GuestAuth", status, msg, "OK" if val == 1 else "WARNING")
            except FileNotFoundError:
                self.add_result("Registre", "GuestAuth", "WARN", "Clé manquante (GuestAuth)", "WARNING")
            winreg.CloseKey(key)
        except Exception as e:
            self.add_result("Registre", "Accès", "ERR", str(e), "CRITICAL")

    def check_event_viewer(self):
        ps_cmd = "Get-WinEvent -FilterHashtable @{LogName='System'; Level=2; StartTime=(Get-Date).AddDays(-1)} -ErrorAction SilentlyContinue | Where-Object {$_.ProviderName -like '*Lanman*' -or $_.ProviderName -like '*SMB*'} | Select-Object -First 3"
        success, out, err = run_command(f"powershell -Command \"{ps_cmd}\"")
        if out:
            self.add_result("Système", "EventViewer", "WARN", "Erreurs réseau détectées dans les logs", "WARNING")
        else:
            self.add_result("Système", "EventViewer", "OK", "Pas d'erreurs critiques récentes")
