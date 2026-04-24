import tkinter as tk
import os
from tkinter import ttk, messagebox, scrolledtext
import threading
from diagnostic import DiagnosticEngine
from repair import RepairEngine
from utils import logger

class AppUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DiagPcNet - Diagnostic & Réparation Partage Windows")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Icône de l'application
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
            if os.path.exists(icon_path):
                self.icon_img = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(False, self.icon_img)
        except Exception as e:
            logger.warning(f"Impossible de charger l'icône : {e}")
        
        self.diag_engine = DiagnosticEngine()
        self.repair_engine = RepairEngine(self.append_log)
        
        self.setup_styles()
        self.create_widgets()
        
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Couleurs modernes
        style.configure("TFrame", background="#f0f2f5")
        style.configure("TLabel", background="#f0f2f5", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"))
        style.configure("Status.TLabel", font=("Segoe UI", 10, "italic"))
        
        style.configure("Action.TButton", padding=10, font=("Segoe UI", 10, "bold"))
        style.configure("Repair.TButton", padding=10, font=("Segoe UI", 10, "bold"), foreground="white", background="#d93025")

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header = ttk.Label(main_frame, text="Diagnostic des Partages Réseau", style="Header.TLabel")
        header.pack(pady=(0, 20))

        # Buttons Frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        self.btn_analyze = ttk.Button(btn_frame, text="🔍 ANALYSER", style="Action.TButton", command=self.start_analysis)
        self.btn_analyze.pack(side=tk.LEFT, padx=5)

        self.btn_repair = ttk.Button(btn_frame, text="🛠️ RÉPARER", style="Action.TButton", command=self.confirm_repair)
        self.btn_repair.pack(side=tk.LEFT, padx=5)
        self.btn_repair.state(['disabled'])

        # Status Indicator
        self.status_var = tk.StringVar(value="Statut : Prêt")
        self.lbl_status = ttk.Label(main_frame, textvariable=self.status_var, style="Status.TLabel")
        self.lbl_status.pack(anchor=tk.W, pady=5)

        # Progress Bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=5)

        # Log Area
        ttk.Label(main_frame, text="Journaux d'opérations :").pack(anchor=tk.W, pady=(10, 0))
        self.log_area = scrolledtext.ScrolledText(main_frame, height=15, font=("Consolas", 9), bg="#1e1e1e", fg="#d4d4d4")
        self.log_area.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.append_log("Bienvenue dans DiagPcNet. Cliquez sur Analyser pour commencer.")

    def append_log(self, message):
        self.log_area.insert(tk.END, f"[{threading.current_thread().name}] {message}\n")
        self.log_area.see(tk.END)

    def start_analysis(self):
        self.btn_analyze.state(['disabled'])
        self.btn_repair.state(['disabled'])
        self.progress.start()
        self.status_var.set("Statut : Analyse en cours...")
        self.log_area.delete('1.0', tk.END)
        self.append_log("Démarrage de l'analyse système...")
        
        thread = threading.Thread(target=self.run_analysis, name="DIAG")
        thread.start()

    def run_analysis(self):
        results, severity = self.diag_engine.run_all()
        
        self.root.after(0, lambda: self.finish_analysis(results, severity))

    def finish_analysis(self, results, severity):
        self.progress.stop()
        self.btn_analyze.state(['!disabled'])
        
        for res in results:
            color = "🟢" if res['severity'] == "OK" else "🟡" if res['severity'] == "WARNING" else "🔴"
            self.append_log(f"{color} {res['category']} > {res['name']}: {res['status']} - {res['message']}")
        
        self.status_var.set(f"Statut : Terminé ({severity})")
        
        if severity != "OK":
            self.btn_repair.state(['!disabled'])
            messagebox.showwarning("Problèmes détectés", f"L'analyse a révélé des points à corriger (Gravité: {severity}).")
        else:
            messagebox.showinfo("Tout est OK", "Aucun problème majeur détecté sur votre configuration de partage.")

    def confirm_repair(self):
        if messagebox.askyesno("Confirmation", "Voulez-vous appliquer les réparations automatiques ?\nCeci modifiera certains réglages système."):
            self.start_repair()

    def start_repair(self):
        self.btn_analyze.state(['disabled'])
        self.btn_repair.state(['disabled'])
        self.progress.start()
        self.status_var.set("Statut : Réparation en cours...")
        
        thread = threading.Thread(target=self.run_repair, name="FIX")
        thread.start()

    def run_repair(self):
        success = self.repair_engine.run_all()
        self.root.after(0, lambda: self.finish_repair(success))

    def finish_repair(self, success):
        self.progress.stop()
        self.btn_analyze.state(['!disabled'])
        self.status_var.set("Statut : Réparations appliquées")
        messagebox.showinfo("Terminé", "Les réparations ont été appliquées.\nIl est recommandé de redémarrer l'ordinateur.")
