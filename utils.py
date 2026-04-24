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
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)

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
            errors='replace'
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
