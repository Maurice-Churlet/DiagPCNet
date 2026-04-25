# Copyright (C) 2026 Maurice
# This program is free software under the GNU GPL v3 license.
# See the LICENSE file for details.

import os
import shutil
import ctypes
from utils import run_command, logger

class CleanerEngine:
    def get_temp_size(self):
        """Calcule la taille totale des fichiers temporaires."""
        paths = [
            os.environ.get('TEMP'),
            os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Temp'),
            os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Prefetch')
        ]
        total_size = 0
        for path in paths:
            if path and os.path.exists(path):
                for root, dirs, files in os.walk(path):
                    for f in files:
                        try:
                            total_size += os.path.getsize(os.path.join(root, f))
                        except:
                            pass
        return total_size / (1024 * 1024) # MB

    def clean_system(self, log_cb=None):
        """Supprime les fichiers temporaires et vide la corbeille."""
        if log_cb: log_cb("Nettoyage des fichiers temporaires...")
        
        paths = [
            os.environ.get('TEMP'),
            os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Temp'),
            os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Prefetch')
        ]
        
        count = 0
        for path in paths:
            if not path or not os.path.exists(path): continue
            for filename in os.listdir(path):
                file_path = os.path.join(path, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                        count += 1
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                        count += 1
                except Exception:
                    pass # Fichiers en cours d'utilisation
        
        if log_cb: log_cb(f"{count} fichiers/dossiers supprimés.")
        
        # Vider la corbeille
        if log_cb: log_cb("Vidage de la corbeille...")
        try:
            # SHEmptyRecycleBinW (None, None, SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND)
            ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 1 | 2 | 4)
            if log_cb: log_cb("Corbeille vidée.")
        except:
            if log_cb: log_cb("Erreur lors du vidage de la corbeille.")
            
        return True

