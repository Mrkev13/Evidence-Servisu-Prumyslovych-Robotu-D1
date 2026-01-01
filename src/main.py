import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import json
import os
from repository import RobotRepository

def load_config():
    # Cesta k configu - upravuje se podle toho, odkud to spouštíš
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_path, 'data', 'config.json')
    
    with open(config_path, 'r') as f:
        return json.load(f)

def get_conn_string(cfg):
    db = cfg['database']
    return f"DRIVER={db['driver']};SERVER={db['server']};DATABASE={db['name']};Trusted_Connection={db['trusted_connection']}"

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.title(self.config['app']['title'])
        self.geometry("900x600")
        
        try:
            conn_str = get_conn_string(self.config)
            self.repo = RobotRepository(conn_str)
        except Exception as e:
            messagebox.showerror("Chyba DB", f"Nelze se připojit: {e}")
            self.destroy()
            return

        self.create_widgets()

    def create_widgets(self):
        # Hlavní notebook (Záložky)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        # 1. Tabulka Robotů
        frame_robots = ttk.Frame(self.notebook)
        self.notebook.add(frame_robots, text='Přehled Robotů')
        self.init_robot_tab(frame_robots)

        # 2. Transakce (Nový Servis)
        frame_service = ttk.Frame(self.notebook)
        self.notebook.add(frame_service, text='Nový Servis (Transakce)')
        self.init_service_tab(frame_service)

        # 3. Sklad a Import
        frame_stock = ttk.Frame(self.notebook)
        self.notebook.add(frame_stock, text='Sklad & Import')
        self.init_stock_tab(frame_stock)

        # 4. Report
        frame_report = ttk.Frame(self.notebook)
        self.notebook.add(frame_report, text='Reporty')
        self.init_report_tab(frame_report)

    # --- TAB 1: ROBOTI ---
    def init_robot_tab(self, parent):
        btn = ttk.Button(parent, text="Načíst data", command=self.load_robots)
        btn.pack(pady=5)
        
        columns = ('ID', 'Model', 'Status', 'Majitel')
        self.tree_robots = ttk.Treeview(parent, columns=columns, show='headings')
        for col in columns: 
            self.tree_robots.heading(col, text=col)
            self.tree_robots.column(col, width=150)
        self.tree_robots.pack(expand=True, fill='both')

    # --- TAB 2: SERVIS (TRANSAKCE) ---
    def init_service_tab(self, parent):
        lbl = ttk.Label(parent, text="Zapsat servisní zásah a odepsat díl", font=("Arial", 12, "bold"))
        lbl.pack(pady=10)

        # Formulář
        frame_form = ttk.Frame(parent)
        frame_form.pack(pady=10)

        # Výběr robota (zjednodušeně zadáváme ID, v PROFI verzi by byl combobox)
        ttk.Label(frame_form, text="ID Robota:").grid(row=0, column=0, padx=5, pady=5)
        self.entry_robot_id = ttk.Entry(frame_form)
        self.entry_robot_id.grid(row=0, column=1)

        # Výběr dílu
        ttk.Label(frame_form, text="ID Dílu (ze skladu):").grid(row=1, column=0, padx=5, pady=5)
        self.entry_part_id = ttk.Entry(frame_form)
        self.entry_part_id.grid(row=1, column=1)

        # Počet kusů
        ttk.Label(frame_form, text="Počet kusů:").grid(row=2, column=0, padx=5, pady=5)
        self.entry_qty = ttk.Entry(frame_form)
        self.entry_qty.grid(row=2, column=1)

        # Popis
        ttk.Label(frame_form, text="Popis závady:").grid(row=3, column=0, padx=5, pady=5)
        self.entry_desc = ttk.Entry(frame_form, width=40)
        self.entry_desc.grid(row=3, column=1)

        # Tlačítko AKCE
        btn_action = ttk.Button(parent, text="PROVEST TRANSAKCI (Uložit + Odepsat)", command=self.run_transaction)
        btn_action.pack(pady=20)

    # --- TAB 3: SKLAD + IMPORT ---
    def init_stock_tab(self, parent):
        # Horní lišta s tlačítky
        frame_btns = ttk.Frame(parent)
        frame_btns.pack(fill='x', pady=5)
        
        ttk.Button(frame_btns, text="Aktualizovat Sklad", command=self.load_stock).pack(side='left', padx=5)
        ttk.Button(frame_btns, text="IMPORT CSV (Naskladnit)", command=self.import_csv).pack(side='right', padx=5)

        columns = ('ID', 'Název', 'Kusů', 'Cena')
        self.tree_stock = ttk.Treeview(parent, columns=columns, show='headings')
        for col in columns: self.tree_stock.heading(col, text=col)
        self.tree_stock.pack(expand=True, fill='both')

    # --- TAB 4: REPORT ---
    def init_report_tab(self, parent):
        btn = ttk.Button(parent, text="Generovat Finanční Report", command=self.show_report)
        btn.pack(pady=20)
        
        self.lbl_report = ttk.Label(parent, text="Zde se zobrazí výsledky...", justify="left")
        self.lbl_report.pack(pady=10)

    # --- LOGIKA ---
    def load_robots(self):
        for i in self.tree_robots.get_children(): self.tree_robots.delete(i)
        # Tady si uprav indexy podle toho, co ti vrací SQL (ID, Model, Status, Owner...)
        for row in self.repo.get_vsechny_roboty():
            # Předpokládám, že VIEW vrací: Model, Status, Owner. Pokud vrací i ID, uprav to.
            # Pro jistotu vypisuju vše, co přijde
            self.tree_robots.insert('', 'end', values=list(row))

    def load_stock(self):
        for i in self.tree_stock.get_children(): self.tree_stock.delete(i)
        for row in self.repo.get_sklad_dilu():
            self.tree_stock.insert('', 'end', values=list(row))

    def run_transaction(self):
        # Validace vstupů (Bod zadání: Ošetření vstupů)
        try:
            r_id = int(self.entry_robot_id.get())
            p_id = int(self.entry_part_id.get())
            qty = int(self.entry_qty.get())
            desc = self.entry_desc.get()
            if not desc: raise ValueError("Chybí popis!")
        except ValueError as e:
            messagebox.showerror("Chyba", f"Špatné zadání: {e}")
            return

        # Volání repozitáře
        success = self.repo.pridat_servis_s_dilem(r_id, p_id, qty, desc)
        if success:
            messagebox.showinfo("Úspěch", "Servis zapsán, díly odečteny (Transakce OK)!")
            self.load_stock() # Obnovit sklad
        else:
            messagebox.showerror("Chyba", "Transakce selhala! (Viz konzole)")

    def import_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if file_path:
            msg = self.repo.import_dilu_z_csv(file_path)
            messagebox.showinfo("Import", msg)
            self.load_stock()

    def show_report(self):
        data = self.repo.get_report_cen()
        text = "MODEL ROBOTA | POČET OPRAV | CELKOVÁ CENA DÍLŮ\n"
        text += "-"*60 + "\n"
        for row in data:
            text += f"{row[0]:<20} | {row[1]:<12} | {row[2]} Kč\n"
        self.lbl_report.config(text=text)

if __name__ == "__main__":
    app = Application()
    app.mainloop()