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

        self.refresh_scripts_list()

        # --- Bas : deux colonnes cote a cote ---
        bottom_frame = ttk.Frame(self.tab_scripts)
        bottom_frame.pack(fill=tk.X, pady=(0, 4))
        bottom_frame.columnconfigure(0, weight=3)
        bottom_frame.columnconfigure(1, weight=1)

        # Colonne gauche : Ajouter / Modifier
        form_frame = ttk.LabelFrame(bottom_frame, text="Ajouter / Modifier", padding=10)
        form_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        form_frame.columnconfigure(1, weight=1)

        ttk.Label(form_frame, text="Titre:").grid(row=0, column=0, sticky="w", pady=2)
        self.script_title_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.script_title_var).grid(row=0, column=1, sticky="ew", padx=5)

        ttk.Label(form_frame, text="Commande:").grid(row=1, column=0, sticky="w", pady=2)
        self.script_cmd_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.script_cmd_var).grid(row=1, column=1, sticky="ew", padx=5)

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

        # Colonne droite : Actions sur la selection
        actions_frame = ttk.LabelFrame(bottom_frame, text="Actions sur la s\u00e9lection", padding=10)
        actions_frame.grid(row=0, column=1, sticky="nsew")

        ttk.Button(actions_frame, text="\u25b6  Lancer",
                   command=self._run_selected_script,   width=16).pack(fill=tk.X, pady=3)
        ttk.Button(actions_frame, text="\u270e  \u00c9diter",
                   command=self._edit_selected_script,  width=16).pack(fill=tk.X, pady=3)
        ttk.Button(actions_frame, text="\u2715  Supprimer",
                   command=self._delete_selected_script, width=16).pack(fill=tk.X, pady=3)

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

