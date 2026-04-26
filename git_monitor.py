# Copyright (C) 2026 Maurice
# This program is free software under the GNU GPL v3 license.
# See the LICENSE file for details.

import os
import subprocess
from utils import run_command, logger

class GitMonitorEngine:
    def is_git_installed(self):
        """Vérifie si git est installé sur le système."""
        try:
            import os
            import subprocess
            subprocess.run(["git", "--version"], 
                           capture_output=True, 
                           creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            return True
        except:
            return False

    def run_git(self, path, args):
        """Exécute une commande git et retourne la sortie."""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=path,
                capture_output=True,
                text=True,
                check=False,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                encoding='utf-8',
                errors='replace'
            )
            return result.stdout.strip()
        except Exception:
            return ""

    def get_repo_info(self, path):
        """Récupère les informations détaillées d'un dépôt Git."""
        # Vérifier si un remote origin existe
        remote = self.run_git(path, ["remote", "get-url", "origin"])
        has_remote = bool(remote)

        name = os.path.basename(path)
        branch = self.run_git(path, ["rev-parse", "--abbrev-ref", "HEAD"])
        
        # Statut local (fichiers modifiés)
        status_raw = self.run_git(path, ["status", "--porcelain"])
        status = "⚠ Dirty" if status_raw else "✔ Clean"
        
        # Dernière activité
        last_commit = self.run_git(path, ["log", "-1", "--format=%cr"])
        
        # Statut de synchronisation (Ahead/Behind)
        sync_status = "Local Only" if not has_remote else "No Upstream"
        
        if has_remote:
            upstream = self.run_git(path, ["rev-parse", "--abbrev-ref", "@{u}"])
            if upstream:
                ahead_behind = self.run_git(path, ["rev-list", "--left-right", "--count", "HEAD..."+upstream])
                if ahead_behind:
                    parts = ahead_behind.split()
                    if len(parts) == 2:
                        ahead, behind = parts
                        if ahead == "0" and behind == "0":
                            sync_status = "Up to date"
                        elif ahead != "0" and behind == "0":
                            sync_status = f"↑ Ahead by {ahead}"
                        elif ahead == "0" and behind != "0":
                            sync_status = f"↓ Behind by {behind}"
                        else:
                            sync_status = f"⇅ Diverged (+{ahead}, -{behind})"

        # Auteur du dernier commit
        last_author = self.run_git(path, ["log", "-1", "--format=%an"])
        
        # Nombre total de commits
        total_commits = self.run_git(path, ["rev-list", "--count", "HEAD"])
        
        # Dernier tag
        latest_tag = self.run_git(path, ["describe", "--tags", "--abbrev=0"])
        if not latest_tag:
            latest_tag = "Aucun"

        return {
            "name": name,
            "path": path,
            "branch": branch,
            "status": status,
            "sync": sync_status,
            "last_commit": last_commit,
            "author": last_author,
            "total_commits": total_commits,
            "latest_tag": latest_tag,
            "remote": remote
        }

    def scan_for_repos(self, base_path, progress_callback=None):
        """Scanne récursivement pour trouver des dépôts Git."""
        repos = []
        found_folders = []
        
        if not os.path.exists(base_path):
            return []

        # Recherche des dossiers .git
        for root, dirs, files in os.walk(base_path):
            if ".git" in dirs:
                found_folders.append(root)
                dirs.remove(".git")
            # Limitation de profondeur pour éviter de scanner tout le disque par erreur
            if root.count(os.sep) - base_path.count(os.sep) > 5:
                del dirs[:]
        
        total = len(found_folders)
        for i, path in enumerate(found_folders):
            if progress_callback:
                progress_callback(i + 1, total, os.path.basename(path))
            
            info = self.get_repo_info(path)
            if info:
                repos.append(info)
        
        return repos

    def commit_and_push(self, path, message):
        """Ajoute tous les fichiers, commit et push vers origin."""
        # 1. Ajouter les fichiers modifiés
        self.run_git(path, ["add", "."])
        # 2. Commit avec le message
        self.run_git(path, ["commit", "-s", "-m", message])
        # 3. Push vers la branche courante
        branch = self.run_git(path, ["rev-parse", "--abbrev-ref", "HEAD"])
        if branch:
            res = self.run_git(path, ["push", "origin", branch])
            return True
        return False
