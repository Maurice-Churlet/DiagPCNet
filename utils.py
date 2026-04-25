# Copyright (C) 2026 Maurice
# This program is free software under the GNU GPL v3 license.
# See the LICENSE file for details.

import os
import sys
import ctypes
import subprocess
import logging
from datetime import datetime

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Relance le script courant avec les droits administrateur via UAC."""
    script = os.path.abspath(sys.argv[0])
    # Arguments supplémentaires entre guillemets
    params = " ".join(f'"{a}"' for a in sys.argv[1:]) if len(sys.argv) > 1 else ""
    full_params = f'"{script}" {params}'.strip()
    ret = ctypes.windll.shell32.ShellExecuteW(
        None,                       # hwnd
        "runas",                    # verbe UAC
        sys.executable,             # python.exe
        full_params,                # "script.py" [args...]
        os.path.dirname(script),    # répertoire de travail
        1                           # SW_SHOWNORMAL
    )
    if ret <= 32:
        logger.error(f"Échec de la relance admin (ShellExecuteW code={ret}).")
        return False
    return True

def run_command(cmd, timeout=30, shell=True):
    """Exécute une commande système avec timeout et capture de sortie."""
    try:
        # Utilisation de powershell pour certaines commandes si nécessaire, 
        # mais ici on reste générique. L'encodage cp850 est typique des consoles FR.
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=timeout, 
            shell=shell,
            encoding='cp850',
            errors='replace',
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"
    except Exception as e:
        return False, "", str(e)

def setup_logger():
    logger = logging.getLogger("DiagPcNet")
    logger.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s', datefmt='%H:%M:%S')
    
    # Console
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    return logger

logger = setup_logger()
