from utils import run_command, logger
import time

class RepairEngine:
    def __init__(self, log_callback=None):
        self.log_callback = log_callback

    def log(self, message):
        logger.info(message)
        if self.log_callback:
            self.log_callback(message)

    def run_all(self):
        self.log(">>> Début de la réparation automatique...")
        
        # 1. Profil Réseau en Privé
        self.log("Réglage du réseau en mode 'Privé'...")
        ps_priv = "Get-NetConnectionProfile | Set-NetConnectionProfile -NetworkCategory Private"
        run_command(f"powershell -Command \"{ps_priv}\"")

        # 2. Activation et démarrage des services
        services = ["fdPHost", "FDResPub", "SSDPSRV", "upnphost", "LanmanWorkstation", "LanmanServer"]
        for svc in services:
            self.log(f"Configuration du service: {svc}...")
            run_command(f"sc config {svc} start= auto")
            run_command(f"net start {svc}")

        # 3. Reset Firewall
        self.log("Réinitialisation des règles de partage du firewall...")
        run_command("netsh advfirewall firewall set rule group=\"Recherche du réseau\" new enable=Yes")
        run_command("netsh advfirewall firewall set rule group=\"Partage de fichiers et d'imprimantes\" new enable=Yes")

        # 4. Registre - Guest Auth
        self.log("Correction du registre (AllowInsecureGuestAuth)...")
        reg_cmd = 'reg add "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\LanmanWorkstation\\Parameters" /v AllowInsecureGuestAuth /t REG_DWORD /d 1 /f'
        run_command(reg_cmd)

        # 5. Flush & Reset Réseau
        self.log("Réinitialisation du cache réseau (DNS, NetBIOS)...")
        run_command("ipconfig /flushdns")
        run_command("nbtstat -R")
        run_command("nbtstat -RR")
        
        self.log("Reset Winsock et IP Stack...")
        run_command("netsh winsock reset")
        run_command("netsh int ip reset")

        self.log(">>> Réparation terminée. Un redémarrage peut être nécessaire.")
        return True

    def full_reset(self):
        """Action de dernier recours."""
        self.log("!!! Exécution du reset réseau complet (netcfg -d) !!!")
        success, out, err = run_command("netcfg -d")
        return success
