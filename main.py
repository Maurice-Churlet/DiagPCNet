# Copyright (C) 2026 Maurice
# This program is free software under the GNU GPL v3 license.
# See the LICENSE file for details.

import tkinter as tk
from ui import AppUI
from utils import is_admin, run_as_admin, logger
import sys

def main():
    # Vérification des droits administrateur
    if not is_admin():
        logger.warning("Droits admin non détectés. Tentative de relance...")
        run_as_admin()
        sys.exit()

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
