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
        result = self.run_git_detailed(path, args)
        return result["stdout"].strip()

    def run_git_detailed(self, path, args):
        """Exécute une commande git et retourne un résultat détaillé."""
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
            return {
                "ok": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": (result.stdout or "").strip(),
                "stderr": (result.stderr or "").strip(),
                "args": args
            }
        except Exception as e:
            return {
                "ok": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "args": args
            }

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

    def commit_and_push(self, path, message, log_callback=None):
        """Ajoute, commit signé et push signé (avec fallback), avec résultat détaillé."""

        def log(level, msg):
            if log_callback:
                log_callback(level, msg)

        result = {
            "success": False,
            "repo_path": path,
            "branch": "",
            "committed": False,
            "pushed": False,
            "signed_push": False,
            "signed_push_unsupported": False,
            "fallback_unsigned_push": False,
            "error_step": "",
            "error_message": ""
        }

        branch_res = self.run_git_detailed(path, ["rev-parse", "--abbrev-ref", "HEAD"])
        branch = branch_res["stdout"] if branch_res["ok"] else ""
        result["branch"] = branch
        if not branch:
            result["error_step"] = "branch"
            result["error_message"] = branch_res["stderr"] or "Impossible de déterminer la branche courante."
            log("ERROR", f"Branche introuvable: {result['error_message']}")
            return result

        log("INFO", f"Préparation du dépôt '{os.path.basename(path)}' sur la branche '{branch}'.")

        add_res = self.run_git_detailed(path, ["add", "."])
        if not add_res["ok"]:
            result["error_step"] = "add"
            result["error_message"] = add_res["stderr"] or "Échec git add"
            log("ERROR", f"git add a échoué: {result['error_message']}")
            return result

        has_staged_changes = self.run_git_detailed(path, ["diff", "--cached", "--quiet"])["returncode"] == 1
        if has_staged_changes:
            commit_res = self.run_git_detailed(path, ["commit", "-S", "-m", message])
            if not commit_res["ok"]:
                result["error_step"] = "commit"
                result["error_message"] = commit_res["stderr"] or commit_res["stdout"] or "Échec commit signé"
                log("ERROR", f"Commit signé échoué: {result['error_message']}")
                return result
            result["committed"] = True
            log("INFO", "Commit signé créé avec succès.")
        else:
            log("INFO", "Aucun changement à commit (index inchangé).")

        push_signed_res = self.run_git_detailed(path, ["push", "--signed", "origin", branch])
        if push_signed_res["ok"]:
            result["pushed"] = True
            result["signed_push"] = True
            result["success"] = True
            log("INFO", "Push signé réussi.")
            return result

        signed_push_error = (push_signed_res["stderr"] or push_signed_res["stdout"] or "").lower()
        if "does not support --signed push".lower() in signed_push_error:
            result["signed_push_unsupported"] = True
            log("INFO", "Serveur distant incompatible avec le push signé (--signed). Passage en fallback non signé.")
        else:
            log("WARNING", f"Push signé échoué ({push_signed_res['returncode']}): {push_signed_res['stderr'] or push_signed_res['stdout']}")

        # Fallback pratique: certains serveurs ne prennent pas en charge le push signé.
        push_fallback_res = self.run_git_detailed(path, ["push", "origin", branch])
        if push_fallback_res["ok"]:
            result["pushed"] = True
            result["fallback_unsigned_push"] = True
            result["success"] = True
            log("WARNING", "Push non signé utilisé en fallback (serveur possiblement incompatible push signé).")
            return result

        result["error_step"] = "push"
        result["error_message"] = push_fallback_res["stderr"] or push_fallback_res["stdout"] or "Échec push"
        log("ERROR", f"Push échoué après fallback: {result['error_message']}")
        return result
