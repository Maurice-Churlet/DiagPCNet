# Copyright (C) 2026 Maurice
# This program is free software under the GNU GPL v3 license.
# See the LICENSE file for details.

import tkinter as tk
from ui import AppUI
from utils import is_admin, run_as_admin, logger
import sys

import ctypes

def hide_console():
    """Cache la fenêtre de console si elle est présente."""
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)
    except:
        pass

def main():
    # Activer la conscience DPI (Haute résolution)
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except:
        try: ctypes.windll.user32.SetProcessDPIAware()
        except: pass

    hide_console()
    # Vérification des droits administrateur
    if not is_admin():
        logger.warning("Droits admin non détectés. Tentative de relance obligatoire...")
        logger.debug(f"Executable: {sys.executable} | Script: {sys.argv[0]}")
        if run_as_admin():
            sys.exit()   # Relance réussie -> on ferme ce process non-admin
        else:
            logger.error("Relance admin échouée ou refusée. Fermeture de l'application.")
            try:
                ctypes.windll.user32.MessageBoxW(
                    0,
                    "DiagPcNet doit être lancé en mode administrateur.\n\nRelancez l'application et acceptez l'élévation UAC.",
                    "Mode administrateur requis",
                    0x10
                )
            except Exception:
                pass
            sys.exit(1)

    logger.info("Démarrage de l'application DiagPcNet")
    
    root = tk.Tk()
    app = AppUI(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        logger.info("Arrêt demandé par l'utilisateur")
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
    finally:
        logger.info("Application fermée")

if __name__ == "__main__":
    main()
