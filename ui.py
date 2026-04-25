# Copyright (C) 2026 Maurice
# This program is free software under the GNU GPL v3 license.
# See the LICENSE file for details.

import tkinter as tk
import os
import json
from tkinter import ttk, messagebox, scrolledtext
import threading
from diagnostic import DiagnosticEngine
from repair import RepairEngine
from benchmark import BenchmarkEngine
from hardware import HardwareEngine
from git_monitor import GitMonitorEngine
from cleaner import CleanerEngine
from repair_tools import RepairToolsEngine
from manager import ManagerEngine
from vault import VaultEngine
from scripts_manager import ScriptsEngine
from utils import logger
import ctypes
import ctypes.wintypes
import psutil
import time
from PIL import Image
import pystray
from pystray import MenuItem as item

class AppUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DiagPcNet - Diagnostic & Réparation Windows")
        
        # Chargement de la configuration (taille/position)
        self.config_path = os.path.join(os.path.dirname(__file__), "config.json")
        self.load_config()
        
        self.root.minsize(800, 600)
        
        # Engines
        self.diag_engine = DiagnosticEngine()
        self.repair_engine = RepairEngine(self.append_log)
        self.benchmark_engine = BenchmarkEngine()
        self.hardware_engine = HardwareEngine()
        self.git_engine = GitMonitorEngine()
        self.cleaner_engine = CleanerEngine()
        self.repair_tools_engine = RepairToolsEngine()
        self.manager_engine = ManagerEngine()
        self.vault_engine = VaultEngine()
        self.scripts_engine = ScriptsEngine()
        
        self.all_repos = [] 
        self.is_monitoring = True
        
        # Icône de l'application
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
            if os.path.exists(icon_path):
                self.icon_img = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(False, self.icon_img)
        except Exception as e:
            logger.warning(f"Impossible de charger l'icône : {e}")
        
        self.setup_styles()
        self.create_widgets()
        
        # Sauvegarde à la fermeture
        self.root.protocol("WM_DELETE_WINDOW", self.on_minimize_to_tray)
        
        # Binds
        self.root.bind("<F1>", lambda e: self.show_help())
        
        # Binds pour réordonner les onglets
        self.notebook.bind("<Button-1>", self.on_tab_press)
        self.notebook.bind("<B1-Motion>", self.on_tab_motion)
        self.notebook.bind("<ButtonRelease-1>", self.on_tab_release)
        self.drag_data = {"item": None, "x": 0}
        
        # Tray Icon
        
        # Tray Icon
        self.tray_icon = None
        self.setup_tray()
        
        # Lancer le monitoring
        self.start_monitoring()

        # Restaurer le mode plein écran APRES que tout soit monté
        # update_idletasks() force le rendu immédiat des widgets avant l'after()
        if getattr(self, 'is_maximized', False):
            self.root.update_idletasks()
            self.root.after(200, lambda: self.root.state('zoomed'))
        
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Couleurs modernes
        bg_color = "#f0f2f5"
        style.configure("TFrame", background=bg_color)
        style.configure("TLabel", background=bg_color, font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground="#1a73e8")
        style.configure("Status.TLabel", font=("Segoe UI", 10, "italic"))
        style.configure("TNotebook", background=bg_color)
        style.configure("TNotebook.Tab", padding=[15, 5], font=("Segoe UI", 10))
        
        style.configure("Action.TButton", padding=10, font=("Segoe UI", 10, "bold"))
        style.configure("Repair.TButton", padding=10, font=("Segoe UI", 10, "bold"), foreground="white", background="#d93025")
        
        style.configure("Storage.Treeview", font=("Segoe UI", 11), rowheight=28)
        style.configure("Storage.Treeview.Heading", font=("Segoe UI", 11, "bold"))

    def create_widgets(self):
        # Notebook (Onglets)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Log Area - Initialisation préventive avant de créer les onglets
        self.log_area = None
        
        self.create_tabs()

        # Restaurer l'onglet précédent
        if hasattr(self, 'last_tab_index'):
            try: self.notebook.select(self.last_tab_index)
            except: pass

        # Shared Status and Progress at bottom
        bottom_frame = ttk.Frame(self.root, padding="10")
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_var = tk.StringVar(value="Prêt")
        self.lbl_status = ttk.Label(bottom_frame, textvariable=self.status_var, style="Status.TLabel")
        self.lbl_status.pack(side=tk.LEFT)

        self.cpu_ram_var = tk.StringVar(value="CPU: --% | RAM: --%")
        ttk.Label(bottom_frame, textvariable=self.cpu_ram_var, font=("Consolas", 9)).pack(side=tk.LEFT, padx=50)

        self.progress = ttk.Progressbar(bottom_frame, mode='indeterminate', length=200)
        self.progress.pack(side=tk.RIGHT, padx=10)

    def create_tabs(self):
        # Définir tous les onglets possibles
        self.tab_definitions = {
            "🌐 Réseau": (self.create_network_tab),
            "💾 Stockage": (self.create_storage_tab),
            "🔌 Périphériques": (self.create_hardware_tab),
            "🐙 Projets Git": (self.create_git_tab),
            "🧹 Maintenance": (self.create_maint_tab),
            "⚙️ Gestion": (self.create_manager_tab),
            "🔐 Coffre": (self.create_vault_tab),
            "📜 Scripts": (self.create_scripts_tab)
        }

        # Dictionnaire frame_name -> widget (pour show/hide)
        self.tab_frames = {}

        # Charger l'ordre depuis la config ou utiliser l'ordre par défaut
        default_order = list(self.tab_definitions.keys())
        saved_order = getattr(self, 'saved_tab_order', [])
        
        # S'assurer de ne pas avoir de doublons et que tous les onglets sont valides
        order = []
        for t in saved_order:
            if t in default_order and t not in order:
                order.append(t)
        for t in default_order:
            if t not in order:
                order.append(t)

        for name in order:
            if name in self.tab_definitions:
                if name in self.tab_frames: continue # Sécurité doublon
                
                frame = ttk.Frame(self.notebook, padding="20")
                self.notebook.add(frame, text=name)
                self.tab_frames[name] = frame
                # On garde une référence au frame
                if "Réseau" in name: self.tab_network = frame
                elif "Stockage" in name: self.tab_storage = frame
                elif "Périphériques" in name: self.tab_hardware = frame
                elif "Projets Git" in name: self.tab_git = frame
                elif "Maintenance" in name: self.tab_maint = frame
                elif "Gestion" in name: self.tab_manager = frame
                elif "Coffre" in name: self.tab_vault = frame
                elif "Scripts" in name: self.tab_scripts = frame
                
                # Appeler la fonction de création
                self.tab_definitions[name]()

        # --- Onglet Paramètres (toujours visible, épinglé en dernier) ---
        self.tab_settings = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(self.tab_settings, text="🛠️ Paramètres")
        self.create_settings_tab()

        # Appliquer les onglets masqués sauvegardés
        hidden = getattr(self, 'hidden_tabs', [])
        for name in hidden:
            if name in self.tab_frames:
                try:
                    self.notebook.tab(self.tab_frames[name], state='hidden')
                except Exception:
                    pass

    def create_settings_tab(self):
        """Volet de configuration : afficher / masquer les onglets."""
        parent = self.tab_settings

        # --- En-tête ---
        h_frame = ttk.Frame(parent)
        h_frame.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(h_frame, text="🛠️ Paramètres de l'interface", style="Header.TLabel").pack(side=tk.LEFT)

        # --- Bloc Visibilité des onglets ---
        vis_frame = ttk.LabelFrame(parent, text="  Onglets visibles  ", padding=15)
        vis_frame.pack(fill=tk.X, pady=10)

        info_lbl = ttk.Label(
            vis_frame,
            text="Cochez les onglets que vous souhaitez afficher. Les modifications sont sauvegardées automatiquement.",
            wraplength=700, font=("Segoe UI", 9, "italic"), foreground="#555"
        )
        info_lbl.pack(anchor="w", pady=(0, 12))

        # Grille de cases à cocher (4 par ligne)
        grid_frame = ttk.Frame(vis_frame)
        grid_frame.pack(fill=tk.X)

        self._tab_visibility_vars = {}  # nom → BooleanVar

        # Icônes et descriptions courtes
        tab_descriptions = {
            "🌐 Réseau":       "Diagnostic & réparation réseau/SMB",
            "💾 Stockage":     "Benchmark & performance disques",
            "🔌 Périphériques": "Audit matériel & pilotes",
            "🐙 Projets Git":  "Moniteur de dépôts Git",
            "🧹 Maintenance":  "Nettoyage & outils Windows",
            "⚙️ Gestion":      "Programmes & démarrage",
            "🔐 Coffre":       "Coffre fort chiffré",
            "📜 Scripts":      "Lanceur de scripts & presse-papiers",
        }

        hidden_now = getattr(self, 'hidden_tabs', [])
        row_idx = 0
        col_idx = 0
        for name, desc in tab_descriptions.items():
            is_visible = name not in hidden_now
            var = tk.BooleanVar(value=is_visible)
            self._tab_visibility_vars[name] = var

            cell = ttk.Frame(grid_frame, relief="flat")
            cell.grid(row=row_idx, column=col_idx, padx=10, pady=6, sticky="nw")

            cb = ttk.Checkbutton(
                cell,
                text=name,
                variable=var,
                command=lambda n=name, v=var: self._on_tab_visibility_toggle(n, v)
            )
            cb.pack(anchor="w")
            ttk.Label(cell, text=desc, font=("Segoe UI", 8), foreground="#888").pack(anchor="w", padx=22)

            col_idx += 1
            if col_idx >= 4:
                col_idx = 0
                row_idx += 1

        # --- Bouton Tout afficher ---
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=10)
        ttk.Button(btn_frame, text="✅ Tout afficher", command=self._show_all_tabs).pack(side=tk.LEFT, padx=5)

        # --- Séparateur et note ---
        sep = ttk.Separator(parent, orient="horizontal")
        sep.pack(fill=tk.X, pady=15)

        ttk.Label(
            parent,
            text="ℹ️  L'onglet Paramètres est toujours visible et ne peut pas être masqué.",
            font=("Segoe UI", 9, "italic"), foreground="#888"
        ).pack(anchor="w")

    def _on_tab_visibility_toggle(self, name, var):
        """Affiche ou masque un onglet selon la case cochée."""
        if name not in self.tab_frames:
            return
        frame = self.tab_frames[name]
        try:
            if var.get():
                self.notebook.tab(frame, state='normal')
            else:
                # S'assurer qu'on ne cache pas l'onglet actif
                current = self.notebook.select()
                if str(current) == str(frame):
                    self.notebook.select(self.tab_settings)
                self.notebook.tab(frame, state='hidden')
            self.save_config()
        except Exception as e:
            logger.warning(f"Erreur toggle onglet '{name}': {e}")

    def _show_all_tabs(self):
        """Rend tous les onglets visibles et coche toutes les cases."""
        for name, frame in self.tab_frames.items():
            try:
                self.notebook.tab(frame, state='normal')
            except Exception:
                pass
            if name in self._tab_visibility_vars:
                self._tab_visibility_vars[name].set(True)
        self.save_config()
        self.status_var.set("Tous les onglets sont maintenant visibles.")

    def create_network_tab(self):
        h_frame = ttk.Frame(self.tab_network)
        h_frame.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(h_frame, text="F1 pour l'aide", foreground="gray", font=("Segoe UI", 8)).pack(side=tk.LEFT)
        header = ttk.Label(h_frame, text="Diagnostic & Réparation Réseau", style="Header.TLabel")
        header.pack(side=tk.LEFT, expand=True)

        desc = ttk.Label(self.tab_network, text="Vérifie et répare les problèmes de partage de fichiers (SMB, Services, Firewall).", wraplength=700)
        desc.pack(pady=10)

        btn_frame = ttk.Frame(self.tab_network)
        btn_frame.pack(pady=20)

        self.btn_analyze = ttk.Button(btn_frame, text="🔍 ANALYSER LE RÉSEAU", style="Action.TButton", command=self.start_analysis)
        self.btn_analyze.pack(side=tk.LEFT, padx=10)

        self.btn_repair = ttk.Button(btn_frame, text="🛠️ RÉPARER LES PARTAGES", style="Action.TButton", command=self.confirm_repair)
        self.btn_repair.pack(side=tk.LEFT, padx=10)
        self.btn_repair.state(['disabled'])

        # Console de log intégrée à l'onglet (agrandie jusqu'en dessous des boutons)
        log_frame = ttk.LabelFrame(self.tab_network, text="Journaux d'opérations", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.log_area = scrolledtext.ScrolledText(log_frame, font=("Consolas", 10), bg="#1e1e1e", fg="#d4d4d4")
        self.log_area.pack(fill=tk.BOTH, expand=True)
        
        # Message de démarrage (déplacé ici car log_area est maintenant prêt)
        self.append_log("Application démarrée. Prêt pour l'analyse.")

    def create_storage_tab(self):
        h_frame = ttk.Frame(self.tab_storage)
        h_frame.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(h_frame, text="F1 pour l'aide", foreground="gray", font=("Segoe UI", 8)).pack(side=tk.LEFT)
        header = ttk.Label(h_frame, text="Benchmark & Performance Disques", style="Header.TLabel")
        header.pack(side=tk.LEFT, expand=True)

        # Selection Drive
        select_frame = ttk.Frame(self.tab_storage)
        select_frame.pack(fill=tk.X, pady=10)

        ttk.Label(select_frame, text="Sélectionner un lecteur :").pack(side=tk.LEFT)
        self.drive_var = tk.StringVar()
        self.drive_combo = ttk.Combobox(select_frame, textvariable=self.drive_var, state="readonly", font=("Segoe UI", 10), width=40)
        self.drive_combo.pack(side=tk.LEFT, padx=10)
        
        self.btn_refresh_drives = ttk.Button(select_frame, text="Actualiser", command=lambda: threading.Thread(target=self.refresh_drives, daemon=True).start())
        self.btn_refresh_drives.pack(side=tk.LEFT)

        # Benchmark Actions
        btn_frame = ttk.Frame(self.tab_storage)
        btn_frame.pack(pady=20)

        self.btn_benchmark = ttk.Button(btn_frame, text="🚀 LANCER LE BENCHMARK", style="Action.TButton", command=self.start_benchmark)
        self.btn_benchmark.pack()

        # Results history (Treeview)
        hist_frame = ttk.Frame(self.tab_storage)
        hist_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        ttk.Label(hist_frame, text="Historique des tests (50 max)", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        cols = ("date", "lecteur", "modele", "media", "bus", "read", "write", "cat")
        self.bench_tree = ttk.Treeview(hist_frame, columns=cols, show="headings", height=8, style="Storage.Treeview")
        self.bench_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        sb = ttk.Scrollbar(hist_frame, orient=tk.VERTICAL, command=self.bench_tree.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.bench_tree.configure(yscrollcommand=sb.set)
        
        self.bench_tree.heading("date", text="Date", command=lambda: self.sort_bench_tree("date", False))
        self.bench_tree.heading("lecteur", text="Lecteur", command=lambda: self.sort_bench_tree("lecteur", False))
        self.bench_tree.heading("modele", text="Modèle", command=lambda: self.sort_bench_tree("modele", False))
        self.bench_tree.heading("media", text="Type", command=lambda: self.sort_bench_tree("media", False))
        self.bench_tree.heading("bus", text="Bus", command=lambda: self.sort_bench_tree("bus", False))
        self.bench_tree.heading("read", text="Lecture (MB/s)", command=lambda: self.sort_bench_tree("read", False))
        self.bench_tree.heading("write", text="Écriture (MB/s)", command=lambda: self.sort_bench_tree("write", False))
        self.bench_tree.heading("cat", text="Catégorie", command=lambda: self.sort_bench_tree("cat", False))
        
        self.bench_tree.column("date", width=150)
        self.bench_tree.column("lecteur", width=80, anchor=tk.CENTER)
        self.bench_tree.column("modele", width=200, anchor=tk.W)
        self.bench_tree.column("media", width=80, anchor=tk.CENTER)
        self.bench_tree.column("bus", width=80, anchor=tk.CENTER)
        self.bench_tree.column("read", width=110, anchor=tk.E)
        self.bench_tree.column("write", width=110, anchor=tk.E)
        self.bench_tree.column("cat", width=180, anchor=tk.W)
        
        self.bench_tree.bind("<Button-3>", self.show_bench_context_menu)
        
        self.refresh_bench_history_ui()

        # Chargement asynchrone des disques au démarrage
        self.drive_combo['values'] = ["Chargement des lecteurs..."]
        self.drive_combo.current(0)
        self.root.after(500, lambda: threading.Thread(target=self.refresh_drives, daemon=True).start())

    def create_hardware_tab(self):
        h_frame = ttk.Frame(self.tab_hardware)
        h_frame.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(h_frame, text="F1 pour l'aide", foreground="gray", font=("Segoe UI", 8)).pack(side=tk.LEFT)
        header = ttk.Label(h_frame, text="Audit Matériel & Santé Système", style="Header.TLabel")
        header.pack(side=tk.LEFT, expand=True)

        btn_frame = ttk.Frame(self.tab_hardware)
        btn_frame.pack(fill=tk.X, pady=10)

        ttk.Button(btn_frame, text="🔎 AUDIT MATÉRIEL", command=self.run_hardware_audit).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="⌨️ LISTER USB", command=self.run_usb_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🩺 PILOTES", command=self.run_driver_check).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔋 BATTERIE", command=self.run_battery_check).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔄 MAJ WINDOWS", command=self.run_update_check).pack(side=tk.LEFT, padx=5)

        self.hardware_info = scrolledtext.ScrolledText(self.tab_hardware, height=15, font=("Consolas", 10), bg="#ffffff")
        self.hardware_info.pack(fill=tk.BOTH, expand=True, pady=10)

    # --- Actions Network ---
    def append_log(self, message):
        """Ajoute un message aux logs de manière thread-safe."""
        if not self.log_area:
            return
            
        thread_name = threading.current_thread().name
        try:
            # Utiliser after() pour s'assurer que l'UI est mise à jour sur le thread principal
            self.root.after(0, lambda: self._safe_append(thread_name, message))
        except Exception:
            pass # L'application est peut-être en train de se fermer

    def _safe_append(self, thread_name, message):
        if self.log_area:
            if self.log_area.winfo_exists():
                try:
                    logger.debug(f"UI Log inserting: [{thread_name}] {message}")
                    self.log_area.config(state=tk.NORMAL)
                    self.log_area.insert(tk.END, f"[{thread_name}] {message}\n")
                    self.log_area.see(tk.END)
                    self.root.update_idletasks() # Force le rafraîchissement
                except tk.TclError as e:
                    logger.error(f"TclError in _safe_append: {e}")
            else:
                logger.error("log_area exists but winfo_exists() is False!")
        else:
            logger.error("log_area is None!")

    def start_analysis(self):
        logger.info("Démarrage de l'analyse réseau demandé par l'utilisateur")
        self.btn_analyze.state(['disabled'])
        self.progress.start()
        self.status_var.set("Analyse réseau en cours...")
        self.append_log("Démarrage de l'analyse réseau...")
        threading.Thread(target=self.run_analysis, daemon=True).start()

    def run_analysis(self):
        results, severity = self.diag_engine.run_all()
        self.root.after(0, lambda: self.finish_analysis(results, severity))

    def finish_analysis(self, results, severity):
        self.progress.stop()
        self.btn_analyze.state(['!disabled'])
        for res in results:
            self.append_log(f"{res['category']} > {res['name']}: {res['status']}")
            
        if severity == "OK":
            self.append_log("✅ Tous les tests réseau sont corrects. Aucun problème détecté.")
        else:
            self.append_log(f"⚠️ Des problèmes ont été détectés (Sévérité : {severity}).")
            
        self.status_var.set(f"Analyse terminée ({severity})")
        if severity != "OK": self.btn_repair.state(['!disabled'])

    def confirm_repair(self):
        if messagebox.askyesno("Confirmation", "Lancer les réparations réseau ?"):
            self.btn_repair.state(['disabled'])
            self.progress.start()
            self.status_var.set("Réparation en cours...")
            threading.Thread(target=self.run_repair, daemon=True).start()

    def run_repair(self):
        success = self.repair_engine.run_all()
        self.root.after(0, lambda: self.finish_repair(success))

    def finish_repair(self, success):
        self.progress.stop()
        self.btn_analyze.state(['!disabled'])
        self.status_var.set("Réparations terminées")
        messagebox.showinfo("OK", "Réparations terminées.")

    # --- Actions Benchmark ---
    def refresh_drives(self):
        self.status_var.set("Recherche des lecteurs...")
        drives = self.benchmark_engine.get_drives()
        vals = [d['display'] for d in drives]
        
        def update_ui():
            self.drive_combo['values'] = vals
            if vals: 
                self.drive_combo.current(0)
                self.status_var.set("Lecteurs à jour")
            else:
                self.drive_combo.set("Aucun lecteur trouvé")
                self.status_var.set("Aucun lecteur détecté")
        
        self.root.after(0, update_ui)

    def start_benchmark(self):
        drive_str = self.drive_var.get()
        if not drive_str: return
        drive = drive_str.split()[0]
        
        self.btn_benchmark.state(['disabled'])
        self.progress.start()
        self.status_var.set(f"Test de vitesse sur {drive}...")
        self.append_log(f"Benchmark lancé sur {drive} (100 MB de données)...")
        
        threading.Thread(target=self.run_benchmark, args=(drive,), daemon=True).start()

    def run_benchmark(self, drive):
        hw_info = self.benchmark_engine.get_drive_hw_info(drive)
        results = self.benchmark_engine.run_speed_test(drive)
        self.root.after(0, lambda: self.finish_benchmark(results, hw_info))

    def finish_benchmark(self, results, hw_info):
        self.progress.stop()
        self.btn_benchmark.state(['!disabled'])
        if results:
            analysis = self.benchmark_engine.get_standard_comparison(results)
            import datetime
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            entry = {
                "date": now,
                "lecteur": self.drive_var.get().split()[0],
                "modele": hw_info.get("model", "Inconnu"),
                "media": hw_info.get("media", "Inconnu"),
                "bus": hw_info.get("bus", "Inconnu"),
                "read": results['read'],
                "write": results['write'],
                "cat": analysis['cat']
            }
            
            if not hasattr(self, 'bench_history'):
                self.bench_history = []
            
            self.bench_history.insert(0, entry)
            # Limite à 50
            if len(self.bench_history) > 50:
                self.bench_history = self.bench_history[:50]
                
            self.save_config()
            self.refresh_bench_history_ui()
            
            self.status_var.set("Benchmark terminé")
        else:
            self.status_var.set("Erreur pendant le benchmark")

    def refresh_bench_history_ui(self):
        if not hasattr(self, 'bench_history'):
            return
        
        for item in self.bench_tree.get_children():
            self.bench_tree.delete(item)
            
        def format_num(val):
            try:
                # Convertit en int et formate avec des espaces pour les milliers
                return f"{int(float(str(val).replace(' ', ''))):,}".replace(",", " ")
            except (ValueError, TypeError):
                return str(val)
                
        for row in self.bench_history:
            self.bench_tree.insert("", tk.END, values=(
                row["date"], 
                row["lecteur"], 
                row.get("modele", "Inconnu"),
                row.get("media", "Inconnu"),
                row.get("bus", "Inconnu"),
                format_num(row.get("read", 0)), 
                format_num(row.get("write", 0)), 
                row.get("cat", "Inconnu")
            ))

    def show_bench_context_menu(self, event):
        item = self.bench_tree.identify_row(event.y)
        if item:
            self.bench_tree.selection_set(item)
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="❌ Effacer cette entrée", command=lambda: self.delete_bench_entry(item))
            menu.post(event.x_root, event.y_root)

    def delete_bench_entry(self, item):
        values = self.bench_tree.item(item, "values")
        if not values: return
        date_val = values[0]
        lecteur_val = values[1]
        
        if hasattr(self, 'bench_history'):
            # Trouver l'index exact pour éviter de supprimer des doublons parfaits par erreur si plusieurs correspondent, 
            # mais date + lecteur est généralement unique.
            self.bench_history = [row for row in self.bench_history if not (row["date"] == date_val and row["lecteur"] == lecteur_val)]
            self.save_config()
            self.refresh_bench_history_ui()

    def sort_bench_tree(self, col, reverse):
        # Récupérer les éléments
        l = [(self.bench_tree.set(k, col), k) for k in self.bench_tree.get_children('')]
        
        # Tentative de conversion numérique pour les colonnes read/write
        if col in ("read", "write"):
            try:
                l.sort(key=lambda t: float(t[0].replace(' ', '')), reverse=reverse)
            except ValueError:
                l.sort(reverse=reverse)
        else:
            l.sort(reverse=reverse)
            
        # Réarranger les items
        for index, (val, k) in enumerate(l):
            self.bench_tree.move(k, '', index)
            
        # Inverser le prochain tri
        self.bench_tree.heading(col, command=lambda: self.sort_bench_tree(col, not reverse))

    # --- Actions Hardware ---
    def run_hardware_audit(self):
        self.hardware_info.delete('1.0', tk.END)
        self.append_log("Audit matériel lancé...")
        def task():
            audit = self.hardware_engine.audit_system()
            text = "--- AUDIT SYSTÈME ---\n\n"
            for k, v in audit.items():
                text += f"[{k}] : {v}\n"
            self.root.after(0, lambda: self.update_hw_info(text))
        threading.Thread(target=task, daemon=True).start()

    def run_usb_list(self):
        self.append_log("Listing des périphériques USB...")
        def task():
            usb = self.hardware_engine.list_usb_devices()
            text = "--- PÉRIPHÉRIQUES USB ---\n\n" + usb
            self.root.after(0, lambda: self.update_hw_info(text))
        threading.Thread(target=task, daemon=True).start()

    def run_driver_check(self):
        self.append_log("Vérification des pilotes...")
        def task():
            drivers = self.hardware_engine.check_drivers_health()
            text = "--- ÉTAT DES PILOTES ---\n\n" + drivers
            self.root.after(0, lambda: self.update_hw_info(text))
        threading.Thread(target=task, daemon=True).start()

    def run_battery_check(self):
        self.append_log("Vérification batterie...")
        def task():
            status = self.hardware_engine.check_battery()
            text = "--- ÉTAT BATTERIE ---\n\n" + status
            self.root.after(0, lambda: self.update_hw_info(text))
        threading.Thread(target=task, daemon=True).start()

    def run_update_check(self):
        self.append_log("Vérification mises à jour Windows...")
        def task():
            status = self.hardware_engine.check_windows_updates()
            text = "--- MISES À JOUR WINDOWS ---\n\n" + status
            self.root.after(0, lambda: self.update_hw_info(text))
        threading.Thread(target=task, daemon=True).start()

    def update_hw_info(self, text):
        self.hardware_info.delete('1.0', tk.END)
        self.hardware_info.insert(tk.END, text)
        self.status_var.set("Information matérielle mise à jour")

    # --- Actions Git Monitor ---
    def create_git_tab(self):
        h_frame = ttk.Frame(self.tab_git)
        h_frame.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(h_frame, text="F1 pour l'aide", foreground="gray", font=("Segoe UI", 8)).pack(side=tk.LEFT)
        header = ttk.Label(h_frame, text="Moniteur de Projets Git", style="Header.TLabel")
        header.pack(side=tk.LEFT, expand=True)

        # Controls
        ctrl_frame = ttk.Frame(self.tab_git)
        ctrl_frame.pack(fill=tk.X, pady=10)

        ttk.Label(ctrl_frame, text="Dossier source :").pack(side=tk.LEFT)
        self.git_dir_var = tk.StringVar(value="C:\\Dev")
        ttk.Entry(ctrl_frame, textvariable=self.git_dir_var, width=40).pack(side=tk.LEFT, padx=10)
        
        self.btn_scan_git = ttk.Button(ctrl_frame, text="SCANNER", command=self.start_git_scan)
        self.btn_scan_git.pack(side=tk.LEFT, padx=5)
        
        # Alerte si Git manque
        self.lbl_git_warning = ttk.Label(ctrl_frame, text="", foreground="red", font=("Segoe UI", 9, "bold"))
        self.lbl_git_warning.pack(side=tk.LEFT, padx=10)
        
        if not self.git_engine.is_git_installed():
            self.lbl_git_warning.config(text="⚠ Git n'est pas installé sur ce PC")
            self.btn_scan_git.state(['disabled'])

        # Search
        search_frame = ttk.Frame(self.tab_git)
        search_frame.pack(fill=tk.X, pady=5)
        ttk.Label(search_frame, text="Rechercher :").pack(side=tk.LEFT)
        self.git_search_var = tk.StringVar()
        self.git_search_var.trace_add("write", lambda *args: self.filter_git_tree())
        ttk.Entry(search_frame, textvariable=self.git_search_var, width=30).pack(side=tk.LEFT, padx=5)

        # Treeview
        table_frame = ttk.Frame(self.tab_git)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        cols = ("name", "branch", "status", "sync", "last_commit")
        self.git_tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        
        self.git_tree.heading("name", text="Dépôt")
        self.git_tree.heading("branch", text="Branche")
        self.git_tree.heading("status", text="Statut Local")
        self.git_tree.heading("sync", text="Synchro")
        self.git_tree.heading("last_commit", text="Activité")

        self.git_tree.column("name", width=150)
        self.git_tree.column("branch", width=100)
        self.git_tree.column("status", width=100)
        self.git_tree.column("sync", width=120)
        self.git_tree.column("last_commit", width=150)

        sb = ttk.Scrollbar(table_frame, orient="vertical", command=self.git_tree.yview)
        self.git_tree.configure(yscrollcommand=sb.set)
        
        self.git_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

    def start_git_scan(self):
        base_path = self.git_dir_var.get()
        if not os.path.exists(base_path):
            messagebox.showerror("Erreur", "Le dossier n'existe pas.")
            return

        self.btn_scan_git.state(['disabled'])
        self.git_tree.delete(*self.git_tree.get_children())
        self.status_var.set("Scan des dépôts Git...")
        self.progress.start()
        
        threading.Thread(target=self.run_git_scan, args=(base_path,), daemon=True).start()

    def run_git_scan(self, path):
        def progress_cb(current, total, name):
            self.root.after(0, lambda: self.status_var.set(f"Analyse {name} ({current}/{total})"))

        repos = self.git_engine.scan_for_repos(path, progress_cb)
        self.root.after(0, lambda: self.finish_git_scan(repos))

    def finish_git_scan(self, repos):
        self.progress.stop()
        self.btn_scan_git.state(['!disabled'])
        self.all_repos = repos
        self.filter_git_tree()
        self.status_var.set(f"Scan terminé. {len(repos)} dépôts trouvés.")

    def filter_git_tree(self):
        query = self.git_search_var.get().lower()
        self.git_tree.delete(*self.git_tree.get_children())
        for r in self.all_repos:
            if query in r["name"].lower() or query in r["remote"].lower() or query in r["branch"].lower():
                self.git_tree.insert("", "end", values=(
                    r["name"], r["branch"], r["status"], r["sync"], r["last_commit"]
                ))

    # --- Actions Monitoring ---
    def start_monitoring(self):
        def monitor_loop():
            while self.is_monitoring:
                try:
                    cpu = psutil.cpu_percent()
                    ram = psutil.virtual_memory().percent
                    self.cpu_ram_var.set(f"CPU: {cpu}% | RAM: {ram}%")
                except:
                    pass
                time.sleep(2)
        threading.Thread(target=monitor_loop, daemon=True).start()

    # --- Actions Maintenance ---
    def create_maint_tab(self):
        h_frame = ttk.Frame(self.tab_maint)
        h_frame.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(h_frame, text="F1 pour l'aide", foreground="gray", font=("Segoe UI", 8)).pack(side=tk.LEFT)
        header = ttk.Label(h_frame, text="Nettoyage & Réparation Système", style="Header.TLabel")
        header.pack(side=tk.LEFT, expand=True)

        # Cleaner
        clean_frame = ttk.LabelFrame(self.tab_maint, text="Nettoyage Disque", padding=10)
        clean_frame.pack(fill=tk.X, pady=10)
        
        self.lbl_temp_size = ttk.Label(clean_frame, text="Calcul de l'espace récupérable...")
        self.lbl_temp_size.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(clean_frame, text="NETTOYER MAINTENANT", command=self.run_system_clean).pack(side=tk.RIGHT, padx=10)
        
        # Repair
        repair_frame = ttk.LabelFrame(self.tab_maint, text="Outils de Réparation Windows", padding=10)
        repair_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(repair_frame, text="LANCER SFC (Réparer fichiers)", command=lambda: self.run_long_task(self.repair_tools_engine.run_sfc)).pack(side=tk.LEFT, padx=5)
        ttk.Button(repair_frame, text="LANCER DISM (Image système)", command=lambda: self.run_long_task(self.repair_tools_engine.run_dism)).pack(side=tk.LEFT, padx=5)

        # Refresh temp size
        self.root.after(1000, self.update_temp_size)

    def update_temp_size(self):
        size = self.cleaner_engine.get_temp_size()
        self.lbl_temp_size.config(text=f"Espace récupérable estimé : {size:.2f} MB")

    def run_system_clean(self):
        if messagebox.askyesno("Confirmation", "Voulez-vous supprimer les fichiers temporaires et vider la corbeille ?"):
            self.cleaner_engine.clean_system(self.append_log)
            self.update_temp_size()
            messagebox.showinfo("OK", "Nettoyage terminé.")

    def run_long_task(self, func):
        self.progress.start()
        def task():
            func(self.append_log)
            self.root.after(0, self.progress.stop)
            self.root.after(0, lambda: messagebox.showinfo("Terminé", "L'opération système est terminée."))
        threading.Thread(target=task, daemon=True).start()

    # --- Actions Manager ---
    def create_manager_tab(self):
        h_frame = ttk.Frame(self.tab_manager)
        h_frame.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(h_frame, text="F1 pour l'aide", foreground="gray", font=("Segoe UI", 8)).pack(side=tk.LEFT)
        header = ttk.Label(h_frame, text="Gestion des Programmes & Démarrage", style="Header.TLabel")
        header.pack(side=tk.LEFT, expand=True)

        btn_frame = ttk.Frame(self.tab_manager)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="LISTER DÉMARRAGE", command=self.show_startup).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="LOGICIELS INSTALLÉS", command=self.show_software).pack(side=tk.LEFT, padx=5)

        self.manager_list = scrolledtext.ScrolledText(self.tab_manager, height=15, font=("Consolas", 10))
        self.manager_list.pack(fill=tk.BOTH, expand=True, pady=10)

    def show_startup(self):
        items = self.manager_engine.get_startup_items()
        text = "--- PROGRAMMES AU DÉMARRAGE ---\n\n"
        for i in items:
            text += f"[{i['name']}] -> {i['path']}\n"
        self.manager_list.delete('1.0', tk.END)
        self.manager_list.insert(tk.END, text)

    def show_software(self):
        self.status_var.set("Récupération de la liste des logiciels...")
        def task():
            sw = self.manager_engine.get_installed_software()
            text = "--- LOGICIELS INSTALLÉS ---\n\n"
            for s in sw:
                text += f"- {s['name']} (v{s['version']})\n"
            self.root.after(0, lambda: self.update_manager_list(text))
        threading.Thread(target=task, daemon=True).start()

    def update_manager_list(self, text):
        self.manager_list.delete('1.0', tk.END)
        self.manager_list.insert(tk.END, text)
        self.status_var.set("Liste des logiciels à jour")

    # --- Actions Vault ---
    def create_vault_tab(self):
        h_frame = ttk.Frame(self.tab_vault)
        h_frame.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(h_frame, text="F1 pour l'aide", foreground="gray", font=("Segoe UI", 8)).pack(side=tk.LEFT)
        header = ttk.Label(h_frame, text="Coffre Fort Sécurisé", style="Header.TLabel")
        header.pack(side=tk.LEFT, expand=True)
        
        self.vault_frame = ttk.Frame(self.tab_vault)
        self.vault_frame.pack(fill=tk.BOTH, expand=True)
        
        if not self.vault_engine.is_initialized():
            self.show_vault_init()
        else:
            self.show_vault_login()

    def show_vault_init(self):
        for w in self.vault_frame.winfo_children(): w.destroy()
        ttk.Label(self.vault_frame, text="Définissez vos deux mots de passe :").pack(pady=5)
        
        ttk.Label(self.vault_frame, text="Vrai Mot de Passe :").pack()
        f1 = ttk.Frame(self.vault_frame)
        f1.pack()
        p1 = ttk.Entry(f1, show="*")
        p1.pack(side=tk.LEFT)
        ttk.Button(f1, text="👁", width=3, command=lambda: self.toggle_pwd(p1)).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(self.vault_frame, text="Mot de Passe d'Illusion (Bidon) :").pack()
        f2 = ttk.Frame(self.vault_frame)
        f2.pack()
        p2 = ttk.Entry(f2, show="*")
        p2.pack(side=tk.LEFT)
        ttk.Button(f2, text="👁", width=3, command=lambda: self.toggle_pwd(p2)).pack(side=tk.LEFT, padx=2)
        
        # Validation par Entrée
        p1.bind("<Return>", lambda e: do_init())
        p2.bind("<Return>", lambda e: do_init())
        
        def do_init():
            if p1.get() and p2.get() and p1.get() != p2.get():
                self.vault_engine.save_vault(p1.get(), [], p2.get(), [{"site": "Banque", "cle": "mettre ici vos informations bancaires"}])
                self.show_vault_login()
            else:
                messagebox.showerror("Erreur", "Les mots de passe doivent être différents et non vides.")
        
        ttk.Button(self.vault_frame, text="CRÉER LE COFFRE", command=do_init).pack(pady=20)

    def show_vault_login(self):
        # Sauvegarder la largeur de colonne avant destruction
        if hasattr(self, 'vault_tree') and self.vault_tree.winfo_exists():
            self.saved_vault_col_w = self.vault_tree.column("site", "width")

        for w in self.vault_frame.winfo_children(): w.destroy()
        
        pwd_var = tk.StringVar()
        f_login = ttk.Frame(self.vault_frame)
        f_login.pack(pady=10)
        entry = ttk.Entry(f_login, textvariable=pwd_var, show="*", width=30)
        entry.pack(side=tk.LEFT)
        ttk.Button(f_login, text="👁", width=3, command=lambda: self.toggle_pwd(entry)).pack(side=tk.LEFT, padx=2)
        entry.focus()
        
        # Validation par Entrée
        entry.bind("<Return>", lambda e: try_login())

        def try_login():
            pwd = pwd_var.get()
            data, is_real = self.vault_engine.unlock(pwd)
            if data is not None:
                self.current_vault_pwd = pwd # Stockage temporaire pour la session
                self.show_vault_content(data, is_real)
            else:
                messagebox.showerror("Erreur", "Mot de passe incorrect")
        
        ttk.Button(self.vault_frame, text="DÉVERROUILLER", command=try_login).pack()

    def show_vault_content(self, data, is_real):
        # Sauvegarder la largeur actuelle avant de rafraîchir
        if hasattr(self, 'vault_tree') and self.vault_tree.winfo_exists():
            self.saved_vault_col_w = self.vault_tree.column("site", "width")

        for w in self.vault_frame.winfo_children(): w.destroy()
        
        # Message de notification fugitif
        self.vault_notify_var = tk.StringVar(value="")
        lbl_notify = ttk.Label(self.vault_frame, textvariable=self.vault_notify_var, foreground="green", font=("Segoe UI", 9, "italic"))
        lbl_notify.pack()

        # Calcul de la largeur optimale pour la première colonne (min 25 chars ~ 200px)
        from tkinter import font as tkfont
        f = tkfont.nametofont("TkDefaultFont")
        
        # On utilise la largeur sauvegardée si elle existe, sinon on calcule
        if hasattr(self, 'saved_vault_col_w'):
            max_w = self.saved_vault_col_w
        else:
            max_w = 200
            for item in data:
                w = f.measure(item.get("site", "Inconnu")) + 20
                if w > max_w: max_w = w

        # Tableau pour les secrets
        columns = ("site", "secret")
        self.vault_tree = ttk.Treeview(self.vault_frame, columns=columns, show="headings", height=10)
        self.vault_tree.heading("site", text="Site / Application")
        self.vault_tree.heading("secret", text="Information (Cliquer pour copier)")
        
        # Site : Largeur fixe/persistante, pas de stretch
        self.vault_tree.column("site", width=max_w, minwidth=100, stretch=False)
        # Secret : Absorbe le reste de la fenêtre
        self.vault_tree.column("secret", width=300, stretch=True)
        
        self.vault_tree.pack(fill=tk.BOTH, expand=True, pady=10)
        
        for item in data:
            self.vault_tree.insert("", "end", values=(item.get("site", "Inconnu"), item.get("cle", "")))
            
        self.vault_tree.bind("<ButtonRelease-1>", self.on_vault_click)
        
        # Formulaire d'édition
        edit_frame = ttk.LabelFrame(self.vault_frame, text="Gérer les secrets", padding=10)
        edit_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(edit_frame, text="Site:").grid(row=0, column=0, sticky="w")
        self.vault_site_var = tk.StringVar()
        ttk.Entry(edit_frame, textvariable=self.vault_site_var).grid(row=0, column=1, sticky="ew", padx=5)
        
        ttk.Label(edit_frame, text="Info:").grid(row=1, column=0, sticky="w")
        self.vault_secret_var = tk.StringVar()
        ttk.Entry(edit_frame, textvariable=self.vault_secret_var).grid(row=1, column=1, sticky="ew", padx=5)
        
        btn_f = ttk.Frame(edit_frame)
        btn_f.grid(row=2, column=1, sticky="e", pady=5)
        
        ttk.Button(btn_f, text="AJOUTER / MAJ", command=lambda: self.save_vault_item(is_real)).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_f, text="SUPPRIMER", command=lambda: self.delete_vault_item(is_real)).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(self.vault_frame, text="VERROUILLER", command=self.show_vault_login).pack(pady=5)

    def on_vault_click(self, event):
        item_id = self.vault_tree.identify_row(event.y)
        if item_id:
            values = self.vault_tree.item(item_id, "values")
            self.vault_site_var.set(values[0])
            self.vault_secret_var.set(values[1])
            self.copy_vault_item(event)

    def save_vault_item(self, is_real):
        site = self.vault_site_var.get()
        secret = self.vault_secret_var.get()
        if not site: return
        
        # On récupère toutes les données actuelles du Treeview
        new_data = []
        updated = False
        for item in self.vault_tree.get_children():
            v = self.vault_tree.item(item, "values")
            if v[0] == site:
                new_data.append({"site": site, "cle": secret})
                updated = True
            else:
                new_data.append({"site": v[0], "cle": v[1]})
        
        if not updated:
            new_data.append({"site": site, "cle": secret})
            
        # On doit sauvegarder via l'engine
        # Attention : pour sauvegarder, on a besoin des DEUX mots de passe.
        # Comme on ne les a pas stockés en clair, on va demander à l'utilisateur 
        # de confirmer son mot de passe actuel pour ré-encrypter ? 
        # NON, on va stocker temporairement le mot de passe de la session actuelle.
        if hasattr(self, 'current_vault_pwd'):
            # Pour simplifier, on ne met à jour que le blob actuel (réel ou illusion)
            # MAIS l'engine.save_vault ré-écrit tout. 
            # On va modifier l'engine pour permettre la mise à jour partielle.
            messagebox.showinfo("Note", "Modification enregistrée pour cette session.")
            self.update_vault_and_refresh(new_data, is_real)
        else:
            messagebox.showerror("Erreur", "Session expirée. Veuillez vous reconnecter.")

    def delete_vault_item(self, is_real):
        site = self.vault_site_var.get()
        if not site: return
        new_data = []
        for item in self.vault_tree.get_children():
            v = self.vault_tree.item(item, "values")
            if v[0] != site:
                new_data.append({"site": v[0], "cle": v[1]})
        self.update_vault_and_refresh(new_data, is_real)

    def update_vault_and_refresh(self, new_data, is_real):
        if self.vault_engine.update_blob(self.current_vault_pwd, new_data, is_real):
            self.show_vault_content(new_data, is_real)
            self.status_var.set("Coffre mis à jour et sauvegardé.")
        else:
            messagebox.showerror("Erreur", "Impossible de sauvegarder le coffre.")

    def copy_vault_item(self, event):
        item_id = self.vault_tree.identify_row(event.y)
        if item_id:
            values = self.vault_tree.item(item_id, "values")
            if values and len(values) > 1:
                secret = values[1]
                import pyperclip
                pyperclip.copy(secret)
                self.vault_notify_var.set(f"✅ '{values[0]}' copié dans le presse-papier")
                # Effacer le message après 3 secondes
                self.root.after(3000, lambda: self.vault_notify_var.set(""))

    def toggle_pwd(self, entry):
        if entry.cget('show') == '*':
            entry.config(show='')
        else:
            entry.config(show='*')

    # --- Actions Scripts ---
    @staticmethod
    def _normalize(text):
        """Supprime les accents et met en minuscules pour la comparaison."""
        import unicodedata
        return unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('ascii').lower()

    def create_scripts_tab(self):
        h_frame = ttk.Frame(self.tab_scripts)
        h_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(h_frame, text="F1 pour l'aide", foreground="gray", font=("Segoe UI", 8)).pack(side=tk.LEFT)
        ttk.Label(h_frame, text="Gestionnaire de Scripts & Presse-papiers", style="Header.TLabel").pack(side=tk.LEFT, expand=True)

        # --- Barre de filtrage (non persistant) ---
        filter_frame = ttk.LabelFrame(self.tab_scripts, text="  Filtres  ", padding=(10, 6))
        filter_frame.pack(fill=tk.X, pady=(0, 8))

        kw_frame = ttk.Frame(filter_frame)
        kw_frame.pack(side=tk.LEFT, padx=(0, 20))
        ttk.Label(kw_frame, text="\U0001f50d Mot-cl\u00e9 :").pack(side=tk.LEFT)
        self.script_filter_kw = tk.StringVar()
        ttk.Entry(kw_frame, textvariable=self.script_filter_kw, width=25).pack(side=tk.LEFT, padx=(6, 4))
        ttk.Button(kw_frame, text="\u2715", width=2,
                   command=lambda: self.script_filter_kw.set("")).pack(side=tk.LEFT)
        self.script_filter_kw.trace_add("write", lambda *_: self.refresh_scripts_list())

        type_frame = ttk.Frame(filter_frame)
        type_frame.pack(side=tk.LEFT)
        ttk.Label(type_frame, text="Type :").pack(side=tk.LEFT, padx=(0, 6))
        self.script_filter_type = tk.StringVar(value="Tous")
        for label, val in [("Tous", "Tous"), ("\u26a1 PowerShell", "PowerShell"),
                           ("\u2699\ufe0f Cach\u00e9", "Hidden"), ("\U0001f4cb Copie", "Copie")]:
            ttk.Radiobutton(type_frame, text=label, variable=self.script_filter_type,
                            value=val, command=self.refresh_scripts_list).pack(side=tk.LEFT, padx=4)

        self.script_filter_count_var = tk.StringVar(value="")
        ttk.Label(filter_frame, textvariable=self.script_filter_count_var,
                  font=("Segoe UI", 9, "italic"), foreground="#666").pack(side=tk.RIGHT, padx=10)

        # --- Tableau Treeview (tri alpha) ---
        tree_frame = ttk.Frame(self.tab_scripts)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        cols = ("title", "mode", "command", "idx")
        self.scripts_tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
                                         selectmode="browse", displaycolumns=("title", "mode", "command"))
        self.scripts_tree.heading("title",   text="Titre \u25b2", anchor="w")
        self.scripts_tree.heading("mode",    text="Type",         anchor="w")
        self.scripts_tree.heading("command", text="Commande",     anchor="w")
        self.scripts_tree.column("title",   width=200, minwidth=120, stretch=False)
        self.scripts_tree.column("mode",    width=120, minwidth=80,  stretch=False)
        self.scripts_tree.column("command", width=400, minwidth=150, stretch=True)

        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.scripts_tree.yview)
        self.scripts_tree.configure(yscrollcommand=sb.set)
        self.scripts_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.scripts_tree.bind("<Double-1>", lambda e: self._edit_selected_script())
        self.scripts_tree.bind("<Button-3>", self._on_script_right_click)

        self.refresh_scripts_list()

        # --- Bas : deux colonnes cote a cote ---
        # --- Bas : trois colonnes ---
        bottom_frame = ttk.Frame(self.tab_scripts)
        bottom_frame.pack(fill=tk.X, pady=(0, 4))
        bottom_frame.columnconfigure(0, weight=0)
        bottom_frame.columnconfigure(1, weight=0)
        bottom_frame.columnconfigure(2, weight=1)

        # Colonne 0 : Actions sur la sélection (Inversé)
        actions_frame = ttk.LabelFrame(bottom_frame, text="Actions sur la s\u00e9lection", padding=10)
        actions_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        ttk.Button(actions_frame, text="\u25b6  Lancer",
                   command=self._run_selected_script,   width=16).pack(fill=tk.X, pady=3)
        ttk.Button(actions_frame, text="\u270e  \u00c9diter",
                   command=self._edit_selected_script,  width=16).pack(fill=tk.X, pady=3)
        ttk.Button(actions_frame, text="\u2715  Supprimer",
                   command=self._delete_selected_script, width=16).pack(fill=tk.X, pady=3)

        # Colonne 1 : Ajouter / Modifier (Inversé)
        form_frame = ttk.LabelFrame(bottom_frame, text="Ajouter / Modifier", padding=10)
        form_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 6))

        ttk.Label(form_frame, text="Titre:").grid(row=0, column=0, sticky="w", pady=2)
        self.script_title_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.script_title_var, width=30).grid(row=0, column=1, sticky="ew", padx=5)

        ttk.Label(form_frame, text="Commande:").grid(row=1, column=0, sticky="w", pady=2)
        self.script_cmd_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.script_cmd_var, width=50).grid(row=1, column=1, sticky="ew", padx=5)

        mode_frame = ttk.Frame(form_frame)
        mode_frame.grid(row=2, column=1, sticky="w", pady=2)
        self.script_mode_var = tk.StringVar(value="PowerShell")
        ttk.Radiobutton(mode_frame, text="PowerShell", variable=self.script_mode_var, value="PowerShell").pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="Cach\u00e9",      variable=self.script_mode_var, value="Hidden").pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="\U0001f4cb Copie", variable=self.script_mode_var, value="Copie").pack(side=tk.LEFT)

        self.script_pause_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(mode_frame, text="Pause", variable=self.script_pause_var).pack(side=tk.LEFT, padx=10)

        btn_row = ttk.Frame(form_frame)
        btn_row.grid(row=3, column=1, sticky="e", pady=(6, 0))
        ttk.Button(btn_row, text="\u2714 ENREGISTRER", command=self.save_current_script).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_row, text="\u2715 Annuler", command=self._clear_script_form).pack(side=tk.LEFT, padx=2)

        # Colonne 2 : Espace vide pour remplir
        ttk.Frame(bottom_frame).grid(row=0, column=2, sticky="nsew")

    # --- Helpers selection Treeview ---
    def _get_selected_real_idx(self):
        sel = self.scripts_tree.selection()
        if not sel:
            return None
        return int(self.scripts_tree.item(sel[0], "values")[3])

    def _run_selected_script(self):
        idx = self._get_selected_real_idx()
        if idx is None:
            self.status_var.set("S\u00e9lectionnez un script dans le tableau.")
            return
        self.run_script_action(self.scripts_engine.scripts[idx])

    def _edit_selected_script(self):
        idx = self._get_selected_real_idx()
        if idx is None:
            self.status_var.set("S\u00e9lectionnez un script \u00e0 \u00e9diter.")
            return
        self.edit_script(self.scripts_engine.scripts[idx], idx)

    def _delete_selected_script(self):
        idx = self._get_selected_real_idx()
        if idx is None:
            self.status_var.set("S\u00e9lectionnez un script \u00e0 supprimer.")
            return
        self.delete_script(idx)

    def _clear_script_form(self):
        self.script_title_var.set("")
        self.script_cmd_var.set("")
        self.script_mode_var.set("PowerShell")
        self.script_pause_var.set(True)
        self.editing_script_idx = -1

    def _on_script_right_click(self, event):
        """Menu contextuel au clic droit sur une ligne."""
        iid = self.scripts_tree.identify_row(event.y)
        if not iid:
            return
            
        # Sélectionner la ligne sous le curseur
        self.scripts_tree.selection_set(iid)
        values = self.scripts_tree.item(iid, "values")
        mode = values[1]  # ex: "⚡ PowerShell", "📋 Copie"
        
        menu = tk.Menu(self.root, tearoff=0)
        
        # Action principale dynamique
        if "Copie" in mode:
            menu.add_command(label="📋 Copier", command=self._run_selected_script)
        else:
            menu.add_command(label="▶ Lancer", command=self._run_selected_script)
            
        menu.add_separator()
        menu.add_command(label="✎ Éditer", command=self._edit_selected_script)
        menu.add_command(label="✕ Supprimer", command=self._delete_selected_script)
        
        menu.post(event.x_root, event.y_root)

    def refresh_scripts_list(self):
        if not hasattr(self, 'scripts_tree'):
            return

        # Memoriser la selection courante (titre) pour la restaurer
        prev_title = None
        sel = self.scripts_tree.selection()
        if sel:
            prev_title = self.scripts_tree.item(sel[0], "values")[0]

        self.scripts_tree.delete(*self.scripts_tree.get_children())

        kw_raw  = getattr(self, 'script_filter_kw',  None)
        typ_var = getattr(self, 'script_filter_type', None)
        kw  = self._normalize(kw_raw.get())  if kw_raw  else ""
        typ = typ_var.get()                   if typ_var else "Tous"

        filtered = [
            (real_idx, s)
            for real_idx, s in enumerate(self.scripts_engine.scripts)
            if (typ == "Tous" or s.get('mode') == typ)
            and (not kw or kw in self._normalize(s.get('title', ''))
                       or kw in self._normalize(s.get('command', '')))
        ]

        # Tri alphabetique insensible aux accents
        filtered.sort(key=lambda t: self._normalize(t[1].get('title', '')))

        total = len(self.scripts_engine.scripts)
        shown = len(filtered)
        if hasattr(self, 'script_filter_count_var'):
            self.script_filter_count_var.set(
                f"{total} script(s)" if shown == total else f"{shown} / {total} script(s)"
            )

        mode_label = {"PowerShell": "\u26a1 PowerShell", "Hidden": "\u2699\ufe0f Cach\u00e9", "Copie": "\U0001f4cb Copie"}
        restore_iid = None
        for real_idx, s in filtered:
            iid = self.scripts_tree.insert("", "end", values=(
                s.get('title', ''),
                mode_label.get(s.get('mode', ''), s.get('mode', '')),
                s.get('command', ''),
                real_idx            # stocke l'indice reel (colonne cachee)
            ))
            if prev_title and s.get('title', '') == prev_title:
                restore_iid = iid

        if restore_iid:
            self.scripts_tree.selection_set(restore_iid)
            self.scripts_tree.see(restore_iid)

    def run_script_action(self, script):
        err = self.scripts_engine.run_script(script)
        if err:
            messagebox.showerror("Erreur", f"\u00c9chec de l'action : {err}")
        else:
            self.status_var.set(f"Action '{script['title']}' ex\u00e9cut\u00e9e.")

    def save_current_script(self):
        title = self.script_title_var.get().strip()
        cmd   = self.script_cmd_var.get().strip()
        if not title or not cmd:
            self.status_var.set("Titre et commande obligatoires.")
            return

        new_script = {
            "title":   title,
            "command": cmd,
            "mode":    self.script_mode_var.get(),
            "pause":   self.script_pause_var.get()
        }

        if hasattr(self, 'editing_script_idx') and self.editing_script_idx >= 0:
            self.scripts_engine.scripts[self.editing_script_idx] = new_script
            self.editing_script_idx = -1
        else:
            self.scripts_engine.scripts.append(new_script)

        self.scripts_engine.save_scripts()
        self._clear_script_form()
        self.refresh_scripts_list()
        self.status_var.set(f"Script '{title}' enregistr\u00e9.")

    def edit_script(self, script, idx):
        self.editing_script_idx = idx
        self.script_title_var.set(script['title'])
        self.script_cmd_var.set(script['command'])
        self.script_mode_var.set(script['mode'])
        self.script_pause_var.set(script.get('pause', False))

    def delete_script(self, idx):
        if messagebox.askyesno("Confirmation", "Supprimer ce script ?"):
            self.scripts_engine.scripts.pop(idx)
            self.scripts_engine.save_scripts()
            self._clear_script_form()
            self.refresh_scripts_list()

    # --- Actions Aide ---
    def show_help(self):
        tab_id = self.notebook.select()
        tab_text = self.notebook.tab(tab_id, "text")
        
        # Extraction simplifiée : on prend le dernier mot (ex: "Réseau")
        clean_tab_name = tab_text.split()[-1]
        print(f"DEBUG: Aide demandée pour '{tab_text}' -> Mot clé: '{clean_tab_name}'")
        
        help_window = tk.Toplevel(self.root)
        help_window.title(f"Aide - {tab_text}")
        help_window.geometry("600x500")
        help_window.transient(self.root)
        
        # Centrage
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_w = self.root.winfo_width()
        main_h = self.root.winfo_height()
        help_window.geometry(f"+{main_x + (main_w-600)//2}+{main_y + (main_h-500)//2}")

        txt_widget = scrolledtext.ScrolledText(help_window, font=("Segoe UI", 11), padx=15, pady=15, bg="white", relief=tk.FLAT)
        txt_widget.pack(fill=tk.BOTH, expand=True)
        
        # Configuration des styles Markdown
        txt_widget.tag_configure("h1", font=("Segoe UI", 16, "bold"), spacing1=10, spacing3=10, foreground="#1a73e8")
        txt_widget.tag_configure("bold", font=("Segoe UI", 11, "bold"))
        txt_widget.tag_configure("bullet", lmargin1=20, lmargin2=35)
        
        aide_path = os.path.join(os.path.dirname(__file__), "aide.md")
        help_text = f"ERREUR : Section '{clean_tab_name}' introuvable."
        
        if os.path.exists(aide_path):
            try:
                with open(aide_path, "r", encoding="utf-8") as f:
                    sections = f.read().split("## Onglet:")
                
                for section in sections:
                    lines = section.strip().split("\n")
                    if lines and clean_tab_name.lower() in lines[0].lower():
                        # Parsing simple du Markdown
                        txt_widget.config(state=tk.NORMAL)
                        for line in lines[1:]:
                            line = line.strip()
                            if not line:
                                txt_widget.insert(tk.END, "\n")
                                continue
                                
                            if line.startswith("**") and line.endswith("**"):
                                txt_widget.insert(tk.END, line.strip("*") + "\n", "h1")
                            elif line.startswith("- "):
                                txt_widget.insert(tk.END, "  • ", "bullet")
                                self._insert_formatted(txt_widget, line[2:] + "\n")
                            else:
                                self._insert_formatted(txt_widget, line + "\n")
                        
                        txt_widget.config(state=tk.DISABLED)
                        return # On a fini
            except Exception as e:
                help_text = f"Erreur technique : {e}"
        
        txt_widget.insert(tk.END, help_text)
        txt_widget.config(state=tk.DISABLED)
        ttk.Button(help_window, text="Fermer l'aide", command=help_window.destroy).pack(pady=10)

    def _insert_formatted(self, widget, text):
        """Helper pour gérer le gras ** au milieu d'une ligne."""
        import re
        parts = re.split(r'(\*\*.*?\*\*)', text)
        for part in parts:
            if part.startswith("**") and part.endswith("**"):
                widget.insert(tk.END, part.strip("*"), "bold")
            else:
                widget.insert(tk.END, part)

    # --- System Tray ---
    def _make_tray_handler(self, script):
        """Closure correcte pour pystray (signature sans argument par défaut)."""
        def _handler(icon, menu_item):
            self.scripts_engine.run_script(script)
        return _handler

    def _build_tray_clipboard_items(self):
        """Construit dynamiquement les sous-items Clipboard du menu tray."""
        clips = [s for s in self.scripts_engine.scripts if s.get('mode') == 'Copie']
        if not clips:
            return (item('(aucun)', None, enabled=False),)
        return tuple(item(s['title'], self._make_tray_handler(s)) for s in clips)

    def _build_tray_command_items(self):
        """Construit dynamiquement les sous-items Commandes du menu tray."""
        cmds = [s for s in self.scripts_engine.scripts if s.get('mode') in ('PowerShell', 'Hidden')]
        if not cmds:
            return (item('(aucun)', None, enabled=False),)
        return tuple(item(s['title'], self._make_tray_handler(s)) for s in cmds)

    def setup_tray(self):
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
            image = Image.open(icon_path)

            menu = pystray.Menu(
                item('Afficher', self.restore_window, default=True),
                pystray.Menu.SEPARATOR,
                item(
                    '📋 Clipboard',
                    pystray.Menu(lambda: self._build_tray_clipboard_items())
                ),
                item(
                    '⚡ Commandes',
                    pystray.Menu(lambda: self._build_tray_command_items())
                ),
                pystray.Menu.SEPARATOR,
                item('Quitter', self.on_closing)
            )

            self.tray_icon = pystray.Icon("DiagPcNet", image, "DiagPcNet", menu)
            # Action sur simple clic (Windows)
            self.tray_icon.action = self.restore_window

            # Démarrer le tray dans un thread séparé
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except Exception as e:
            logger.warning(f"Erreur Tray Icon : {e}")

    def on_minimize_to_tray(self):
        # Sauvegarder la config AVANT de cacher la fenêtre
        self.save_config()
        
        # Sécurité : Verrouiller le coffre lors de la réduction
        if hasattr(self, 'current_vault_pwd'):
            del self.current_vault_pwd
        self.show_vault_login()
        
        self.root.withdraw() # Cache la fenêtre
        self.status_var.set("Application réduite et configuration sauvegardée")

    def restore_window(self):
        def _do_restore():
            self.root.deiconify()
            # Ré-appliquer le mode plein-écran si c'était le cas avant
            if getattr(self, 'is_maximized', False):
                self.root.state('zoomed')
            self.root.lift()
            self.root.focus_force()
        self.root.after(0, _do_restore)

    # --- Persistance ---
    def load_config(self):
        default_geom = "900x700+100+100"
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    config = json.load(f)
                    w, h = config.get("width", 900), config.get("height", 700)
                    x, y = config.get("x", 100), config.get("y", 100)
                    self.last_tab_index = config.get("last_tab", 0)
                    self.saved_vault_col_w = config.get("vault_col_w", 200)
                    self.saved_tab_order = config.get("tab_order", [])
                    self.is_maximized = config.get("maximized", False)
                    self.hidden_tabs = config.get("hidden_tabs", [])
                    self.bench_history = config.get("bench_history", [])
                    
                    # Validation Windows Native pour multi-écrans
                    try:
                        has_monitor = ctypes.windll.user32.MonitorFromPoint(ctypes.wintypes.POINT(x + 50, y + 50), 0)
                        if not has_monitor:
                            screen_w = self.root.winfo_screenwidth()
                            screen_h = self.root.winfo_screenheight()
                            x = (screen_w - w) // 2
                            y = (screen_h - h) // 2
                    except:
                        pass
                        
                    self.root.geometry(f"{w}x{h}+{x}+{y}")
                    # Ne pas appliquer zoomed ici : les widgets ne sont pas encore construits.
                    # La restauration se fait à la fin de __init__ via _apply_maximized().
            else:
                self.root.geometry(default_geom)
        except Exception as e:
            logger.warning(f"Erreur chargement config: {e}")
            self.root.geometry(default_geom)

    # --- Actions Réorganiser Onglets ---
    def on_tab_press(self, event):
        element = self.notebook.identify(event.x, event.y)
        if element == "label":
            index = self.notebook.index(f"@{event.x},{event.y}")
            self.drag_data["item"] = index
            self.drag_data["x"] = event.x

    def on_tab_motion(self, event):
        if self.drag_data["item"] is None: return
        
        # Détecter si on survole un autre onglet
        target_index = self.notebook.index(f"@{event.x},{event.y}")
        if target_index != self.drag_data["item"]:
            # On déplace physiquement l'onglet
            tab_text = self.notebook.tab(self.drag_data["item"], "text")
            tab_id = self.notebook.tabs()[self.drag_data["item"]]
            
            # Insérer à la nouvelle position
            self.notebook.insert(target_index, tab_id)
            self.drag_data["item"] = target_index

    def on_tab_release(self, event):
        self.drag_data["item"] = None
        self.status_var.set("Ordre des onglets mis à jour.")

    # --- Fin ---
    def on_closing(self):
        self.is_monitoring = False
        self.save_config()
        
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.destroy()
        sys.exit()

    def save_config(self):
        try:
            current_state = self.root.state()

            # Ignorer si iconifié (barre des tâches)
            if current_state == 'iconic':
                return

            if current_state == 'withdrawn':
                # La fenêtre est cachée dans le tray.
                # On utilise l'état mémorisé (mis à jour à chaque save_config visible).
                is_max = getattr(self, 'is_maximized', False)
            else:
                is_max = (current_state == 'zoomed')
            
            if is_max:
                # En mode zoomed, Tkinter renvoie les coords plein-écran.
                # On préserve les dimensions normales déjà enregistrées.
                prev = getattr(self, '_normal_geometry', None)
                if prev:
                    parts = prev.replace('+', 'x').split('x')
                else:
                    # Fallback : valeurs raisonnables par défaut
                    parts = ["900", "700", "100", "100"]
            else:
                geom = self.root.geometry()  # "WxH+X+Y"
                parts = geom.replace('+', 'x').split('x')
                # Mémoriser la dernière géométrie normale (non-maximisée)
                self._normal_geometry = self.root.geometry()

            # Collecter les onglets actuellement masqués
            hidden = []
            if hasattr(self, 'tab_frames'):
                for name, frame in self.tab_frames.items():
                    try:
                        if self.notebook.tab(frame, 'state') == 'hidden':
                            hidden.append(name)
                    except Exception:
                        pass
            
            config = {
                "width": int(parts[0]),
                "height": int(parts[1]),
                "x": int(parts[2]),
                "y": int(parts[3]),
                "last_tab": self.notebook.index(self.notebook.select()),
                "vault_col_w": self.vault_tree.column("site", "width") if hasattr(self, 'vault_tree') and self.vault_tree.winfo_exists() else getattr(self, 'saved_vault_col_w', 200),
                "tab_order": [self.notebook.tab(i, "text") for i in range(self.notebook.index("end"))],
                "maximized": is_max,
                "hidden_tabs": hidden,
                "bench_history": getattr(self, 'bench_history', [])
            }
            
            with open(self.config_path, "w") as f:
                json.dump(config, f)
            
            # Mettre à jour is_maximized en mémoire (utilisé par restore_window)
            self.is_maximized = is_max
        except Exception as e:
            logger.warning(f"Erreur sauvegarde config: {e}")
