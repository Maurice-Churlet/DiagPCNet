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
from utils import logger

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
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
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

    def create_widgets(self):
        # Notebook (Onglets)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tab 1: Réseau
        self.tab_network = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(self.tab_network, text="🌐 Réseau")
        self.create_network_tab()

        # Tab 2: Stockage & Benchmark
        self.tab_storage = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(self.tab_storage, text="💾 Stockage")
        self.create_storage_tab()

        # Tab 3: Matériel & Audit
        self.tab_hardware = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(self.tab_hardware, text="🔌 Périphériques")
        self.create_hardware_tab()

        # Shared Status and Progress at bottom
        bottom_frame = ttk.Frame(self.root, padding="10")
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_var = tk.StringVar(value="Prêt")
        self.lbl_status = ttk.Label(bottom_frame, textvariable=self.status_var, style="Status.TLabel")
        self.lbl_status.pack(side=tk.LEFT)

        self.progress = ttk.Progressbar(bottom_frame, mode='indeterminate', length=200)
        self.progress.pack(side=tk.RIGHT, padx=10)

        # Log Area (always visible at bottom or in a separate expandable frame?)
        # Let's put it in a separate frame
        log_frame = ttk.LabelFrame(self.root, text="Journaux d'opérations", padding="5")
        log_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=(0, 10))
        
        self.log_area = scrolledtext.ScrolledText(log_frame, height=8, font=("Consolas", 9), bg="#1e1e1e", fg="#d4d4d4")
        self.log_area.pack(fill=tk.BOTH, expand=True)
        
        self.append_log("Application démarrée. Bienvenue Maurice.")

    def create_network_tab(self):
        header = ttk.Label(self.tab_network, text="Diagnostic des Partages Réseau", style="Header.TLabel")
        header.pack(pady=(0, 20))

        desc = ttk.Label(self.tab_network, text="Vérifie et répare les problèmes de partage de fichiers (SMB, Services, Firewall).", wraplength=700)
        desc.pack(pady=10)

        btn_frame = ttk.Frame(self.tab_network)
        btn_frame.pack(pady=20)

        self.btn_analyze = ttk.Button(btn_frame, text="🔍 ANALYSER LE RÉSEAU", style="Action.TButton", command=self.start_analysis)
        self.btn_analyze.pack(side=tk.LEFT, padx=10)

        self.btn_repair = ttk.Button(btn_frame, text="🛠️ RÉPARER LES PARTAGES", style="Action.TButton", command=self.confirm_repair)
        self.btn_repair.pack(side=tk.LEFT, padx=10)
        self.btn_repair.state(['disabled'])

    def create_storage_tab(self):
        header = ttk.Label(self.tab_storage, text="Benchmark Disque & USB", style="Header.TLabel")
        header.pack(pady=(0, 20))

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

        # Results area
        self.bench_results_frame = ttk.LabelFrame(self.tab_storage, text="Résultats du Test", padding="10")
        self.bench_results_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.lbl_bench_write = ttk.Label(self.bench_results_frame, text="Écriture : -- MB/s", font=("Segoe UI", 12))
        self.lbl_bench_write.pack(pady=5)
        
        self.lbl_bench_read = ttk.Label(self.bench_results_frame, text="Lecture : -- MB/s", font=("Segoe UI", 12))
        self.lbl_bench_read.pack(pady=5)

        self.lbl_bench_comp = ttk.Label(self.bench_results_frame, text="Catégorie détectée : --", font=("Segoe UI", 11, "bold"), foreground="#1a73e8")
        self.lbl_bench_comp.pack(pady=(10, 5))

        self.lbl_bench_desc = ttk.Label(self.bench_results_frame, text="", wraplength=600, font=("Segoe UI", 10, "italic"), justify=tk.CENTER)
        self.lbl_bench_desc.pack(pady=5)

        # Chargement asynchrone des disques au démarrage
        self.drive_combo['values'] = ["Chargement des lecteurs..."]
        self.drive_combo.current(0)
        self.root.after(500, lambda: threading.Thread(target=self.refresh_drives, daemon=True).start())

    def create_hardware_tab(self):
        header = ttk.Label(self.tab_hardware, text="Audit Système & Périphériques", style="Header.TLabel")
        header.pack(pady=(0, 20))

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
        self.log_area.insert(tk.END, f"[{threading.current_thread().name}] {message}\n")
        self.log_area.see(tk.END)

    def start_analysis(self):
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
        results = self.benchmark_engine.run_speed_test(drive)
        self.root.after(0, lambda: self.finish_benchmark(results))

    def finish_benchmark(self, results):
        self.progress.stop()
        self.btn_benchmark.state(['!disabled'])
        if results:
            self.lbl_bench_write.config(text=f"Écriture : {results['write']:.2f} MB/s")
            self.lbl_bench_read.config(text=f"Lecture : {results['read']:.2f} MB/s")
            analysis = self.benchmark_engine.get_standard_comparison(results)
            self.lbl_bench_comp.config(text=f"Catégorie détectée : {analysis['cat']}")
            self.lbl_bench_desc.config(text=analysis['desc'])
            self.append_log(f"Benchmark terminé. Résultat: {analysis['cat']}")
            self.status_var.set("Benchmark terminé")
        else:
            self.status_var.set("Erreur pendant le benchmark")

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

    # --- Persistance ---
    def load_config(self):
        default_geom = "900x700+100+100"
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    config = json.load(f)
                    w, h = config.get("width", 900), config.get("height", 700)
                    x, y = config.get("x", 100), config.get("y", 100)
                    
                    # Validation multi-écrans
                    # On vérifie si le point (x,y) est visible sur le bureau virtuel
                    v_x = self.root.winfo_vrootx()
                    v_y = self.root.winfo_vrooty()
                    v_w = self.root.winfo_vrootwidth()
                    v_h = self.root.winfo_vrootheight()
                    
                    if not (v_x <= x <= v_x + v_w and v_y <= y <= v_y + v_h):
                        # Hors écran, on réinitialise au centre de l'écran principal
                        self.root.geometry(f"{w}x{h}")
                    else:
                        self.root.geometry(f"{w}x{h}+{x}+{y}")
            else:
                self.root.geometry(default_geom)
        except Exception as e:
            logger.warning(f"Erreur chargement config: {e}")
            self.root.geometry(default_geom)

    def on_closing(self):
        try:
            # Récupérer la géométrie actuelle
            geom = self.root.geometry() # format "WxH+X+Y"
            parts = geom.replace('x', '+').split('+')
            config = {
                "width": int(parts[0]),
                "height": int(parts[1]),
                "x": int(parts[2]),
                "y": int(parts[3])
            }
            with open(self.config_path, "w") as f:
                json.dump(config, f)
        except Exception as e:
            logger.warning(f"Erreur sauvegarde config: {e}")
        
        self.root.destroy()
