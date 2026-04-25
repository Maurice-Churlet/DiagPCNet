import tkinter as tk
from tkinter import scrolledtext
import threading
import time

def test_ui():
    root = tk.Tk()
    
    log_area = scrolledtext.ScrolledText(root, font=("Consolas", 10), bg="#1e1e1e", fg="#d4d4d4")
    log_area.pack(fill=tk.BOTH, expand=True)
    
    def _safe_append(thread_name, message):
        if log_area and log_area.winfo_exists():
            try:
                log_area.insert(tk.END, f"[{thread_name}] {message}\n")
                log_area.see(tk.END)
                root.update_idletasks()
                print("Inserted:", message)
            except tk.TclError as e:
                print("TclError:", e)
    
    def append_log(message):
        thread_name = threading.current_thread().name
        root.after(0, lambda: _safe_append(thread_name, message))

    append_log("Application démarrée.")
    
    def run_analysis():
        time.sleep(1)
        append_log("Analysis step 1")
        time.sleep(1)
        append_log("Analysis step 2")

    threading.Thread(target=run_analysis, daemon=True).start()
    
    # Run loop for 3 seconds then exit
    root.after(3500, root.destroy)
    root.mainloop()

test_ui()
