# Copyright (C) 2026 Maurice
# This program is free software under the GNU GPL v3 license.
# See the LICENSE file for details.

import os
import time
import shutil
import platform
import json
from utils import run_command, logger

class BenchmarkEngine:
    def __init__(self):
        self.standards = {
            "USB 2.0": {"write": 10, "read": 30},
            "USB 3.0": {"write": 50, "read": 100},
            "USB 3.1 Gen2": {"write": 300, "read": 500},
            "HDD (SATA)": {"write": 80, "read": 100},
            "SSD (SATA)": {"write": 400, "read": 500},
            "SSD (NVMe Gen3)": {"write": 1500, "read": 2500},
            "SSD (NVMe Gen4)": {"write": 4000, "read": 6000},
        }

    def get_drives(self):
        """Liste les lecteurs logiques et leurs types de manière lisible."""
        drives = []
        ps_cmd = "Get-WmiObject Win32_LogicalDisk | Select-Object DeviceID, VolumeName, DriveType"
        success, out, _ = run_command(f"powershell -Command \"{ps_cmd}\"")
        
        if success:
            lines = out.splitlines()
            for line in lines:
                if ":" in line:
                    parts = line.split()
                    if len(parts) >= 1:
                        drive_id = parts[0]
                        # Détermination du type
                        dtype = "Inconnu"
                        if "2" in line: dtype = "USB / Amovible"
                        elif "3" in line: dtype = "Disque Fixe"
                        elif "4" in line: dtype = "Réseau"
                        
                        # Récupération du label (VolumeName)
                        label = ""
                        if len(parts) > 1 and not parts[-1].isdigit():
                            label = parts[1]
                        
                        display_name = f"{drive_id} [{label}] - {dtype}" if label else f"{drive_id} - {dtype}"
                        drives.append({"id": drive_id, "display": display_name})
        return drives

    def get_drive_hw_info(self, drive_letter):
        """Récupère les informations matérielles du disque (Modèle, Type, Bus)"""
        # Drive letter expected as 'C:'
        letter = drive_letter.replace(':', '')
        ps_cmd = f"Get-Partition | Where-Object DriveLetter -eq '{letter}' | Get-Disk | Get-PhysicalDisk | Select-Object MediaType, BusType, Model | ConvertTo-Json"
        success, out, _ = run_command(f"powershell -Command \"{ps_cmd}\"")
        if success and out.strip():
            try:
                # If multiple disks back a single partition (e.g. Storage Spaces), it might return an array.
                data = json.loads(out)
                if isinstance(data, list):
                    data = data[0]
                return {
                    "model": data.get("Model", "Inconnu").strip(),
                    "media": data.get("MediaType", "Inconnu"),
                    "bus": data.get("BusType", "Inconnu")
                }
            except json.JSONDecodeError:
                pass
        return {"model": "Inconnu", "media": "Inconnu", "bus": "Inconnu"}

    def run_speed_test(self, drive_path, file_size_mb=100):
        """Effectue un test de vitesse en écriture et lecture."""
        test_file = os.path.join(drive_path, "diagpcnet_test.tmp")
        data = os.urandom(1024 * 1024) # 1 MB of random data
        
        # Test Écriture
        start_time = time.time()
        try:
            with open(test_file, 'wb') as f:
                for _ in range(file_size_mb):
                    f.write(data)
            write_duration = time.time() - start_time
            write_speed = file_size_mb / write_duration
        except Exception as e:
            logger.error(f"Erreur écriture: {e}")
            return None

        # Test Lecture
        start_time = time.time()
        try:
            with open(test_file, 'rb') as f:
                while f.read(1024 * 1024):
                    pass
            read_duration = time.time() - start_time
            read_speed = file_size_mb / read_duration
        except Exception as e:
            logger.error(f"Erreur lecture: {e}")
            return None
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

        return {"write": write_speed, "read": read_speed}

    def get_standard_comparison(self, results):
        """Fournit une analyse compréhensible pour un non-initié."""
        r = results["read"]
        
        if r > 3000: 
            return {
                "cat": "SSD (NVMe Gen4) - Ultra Rapide",
                "desc": "Le top du top. Idéal pour tout : Windows ultra-réactif, montage vidéo 4K/8K et gaming intensif. Parfait pour un Dual Boot haute performance."
            }
        elif r > 1500: 
            return {
                "cat": "SSD (NVMe Gen3) - Très Rapide",
                "desc": "Excellent pour un PC moderne. Windows démarre en quelques secondes. Très confortable pour le montage vidéo et le Dual Boot."
            }
        elif r > 300: 
            return {
                "cat": "SSD (SATA) - Rapide",
                "desc": "Performances solides. Idéal pour un usage quotidien fluide (Web, Bureautique). Convient parfaitement pour installer un second système (Dual Boot)."
            }
        elif r > 80: 
            return {
                "cat": "Disque Dur (HDD) ou USB 3.0 - Correct",
                "desc": "Convient pour le stockage de films HD et photos. Trop lent pour Windows aujourd'hui. Déconseillé pour un Dual Boot (sera poussif)."
            }
        else: 
            return {
                "cat": "USB 2.0 / Vieux Disque - Très Lent",
                "desc": "Uniquement pour du stockage de documents ou petits fichiers. Déconseillé pour la vidéo 4K ou l'installation d'un système."
            }
