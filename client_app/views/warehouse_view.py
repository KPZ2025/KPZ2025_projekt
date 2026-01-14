import customtkinter as ctk
import tkinter.messagebox as msg
from api_service import wyslij_transakcje

class WarehouseView(ctk.CTkFrame):
    def __init__(self, parent, app_controller):
        super().__init__(parent, fg_color="transparent")
        self.app = app_controller
        self.pack(fill="both", expand=True)
        self.create_widgets()

    def create_widgets(self):
        container = ctk.CTkFrame(self, fg_color="transparent"); container.pack(fill="both", expand=True)
        
        top_bar = ctk.CTkFrame(container, height=70, fg_color="#1a1a1a", corner_radius=10)
        top_bar.pack(fill="x", side="top", pady=(0, 10))
        ctk.CTkLabel(top_bar, text="MAGAZYN GŁÓWNY", font=("Impact", 24), text_color="#F2A900").pack(side="left", padx=20)
        ctk.CTkButton(top_bar, text="Wyjdź", command=self.app.pokaz_ekran_logowania, fg_color="#cf3030").pack(side="right", padx=20)
        
        grid = ctk.CTkFrame(container, fg_color="transparent"); grid.pack(fill="both", expand=True)
        grid.grid_columnconfigure(0, weight=8); grid.grid_columnconfigure(1, weight=2); grid.grid_rowconfigure(0, weight=1)
        
        left = ctk.CTkFrame(grid, fg_color="transparent"); left.grid(row=0, column=0, sticky="nsew", padx=(0,10))
        header_left = ctk.CTkFrame(left, fg_color="transparent"); header_left.pack(fill="x", pady=5)
        ctk.CTkLabel(header_left, text="STAN ZASOBÓW", font=("Roboto", 16, "bold")).pack(side="left")
        ctk.CTkButton(header_left, text="+ PRZYJMIJ DOSTAWĘ", width=150, fg_color="#2cc985", text_color="black", 
                      command=self.pokaz_popup_dostawy).pack(side="right")
        
        self.inv_sc = ctk.CTkScrollableFrame(left, fg_color="#2b2b2b"); self.inv_sc.pack(fill="both", expand=True)
        
        right = ctk.CTkFrame(grid, fg_color="#111", corner_radius=10, border_color="#333", border_width=2); right.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(right, text="HISTORIA ZAMÓWIEŃ", font=("Impact", 18), text_color="#00E676").pack(pady=10)
        self.ord_sc = ctk.CTkScrollableFrame(right, fg_color="transparent"); self.ord_sc.pack(fill="both", expand=True)
        
        self.odswiez_magazyn()

    def odswiez_magazyn(self):
        for w in self.inv_sc.winfo_children(): w.destroy()
        for p in self.app.produkty_db: 
            self.stworz_kafelek_magazynowy(self.inv_sc, p)
            
        for w in self.ord_sc.winfo_children(): w.destroy()
        if not self.app.historia_zamowien: 
            ctk.CTkLabel(self.ord_sc, text="Brak zamówień.", text_color="gray").pack(pady=50)
        else:
            for z in self.app.historia_zamowien: 
                self.stworz_karte_zamowienia(self.ord_sc, z)

    def stworz_kafelek_magazynowy(self, p, d):
        c = ctk.CTkFrame(p, fg_color="#3a3a3a"); c.pack(fill="x", pady=5)
        header = ctk.CTkFrame(c, fg_color="transparent"); header.pack(fill="x", padx=15, pady=5)
        
        qty = d.get('qty', 0)
        name = d.get('name', 'Unknown')
        unit = d.get('unit', 'szt')
        
        max_cap = 100 
        ratio = qty / max_cap

        if ratio > 1.0: stat = "NADMIAR"; col = "#3B8ED0"; bar_val = 1.0
        elif ratio < 0.2: stat = "KRYTYCZNY"; col = "#FF1744"; bar_val = ratio
        elif ratio < 0.5: stat = "UWAGA"; col = "#FF9100"; bar_val = ratio
        else: stat = "NORMA"; col = "#00E676"; bar_val = ratio

        ctk.CTkLabel(header, text=name, font=("Roboto", 20, "bold")).pack(side="left")
        ctk.CTkLabel(header, text=stat, font=("Roboto", 12, "bold"), text_color=col).pack(side="right")
        
        bar = ctk.CTkProgressBar(c, progress_color=col); bar.set(bar_val); bar.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(c, text=f"Stan: {qty} {unit}", font=("Roboto", 14), text_color="#aaa").pack(fill="x", padx=15, pady=5)

    def stworz_karte_zamowienia(self, p, d):
        c = ctk.CTkFrame(p, fg_color="#1a1a1a", border_color="#00E676", border_width=1); c.pack(fill="x", pady=5)
        ctk.CTkLabel(c, text=d['user'], font=("Arial", 14, "bold"), text_color="white").pack()
        ctk.CTkLabel(c, text=d['czas'], font=("Roboto", 10), text_color="gray").pack()
        for i in d['produkty']: ctk.CTkLabel(c, text=f"• {i}").pack()

    def pokaz_popup_dostawy(self):
        window = ctk.CTkToplevel(self)
        window.geometry("300x250")
        window.attributes("-topmost", True)
        
        ctk.CTkLabel(window, text="PRZYJĘCIE DOSTAWY", font=("Impact", 18)).pack(pady=15)
        
        prod_names = [p['name'] for p in self.app.produkty_db]
        combo_prod = ctk.CTkOptionMenu(window, values=prod_names); combo_prod.pack(pady=10)
        entry_qty = ctk.CTkEntry(window, placeholder_text="Ilość"); entry_qty.pack(pady=10)

        def zapisz():
            try:
                ilosc = int(entry_qty.get())
                nazwa = combo_prod.get()
                prod = next((p for p in self.app.produkty_db if p['name'] == nazwa), None)
                if prod:
                    if wyslij_transakcje(prod['id'], ilosc, self.app.aktualny_uzytkownik):
                        self.app.odswiez_dane()
                        self.odswiez_magazyn()
                        window.destroy()
                        self.app.pokaz_custom_popup("DOSTAWA PRZYJĘTA", f"Zaktualizowano: {nazwa}")
                    else:
                        msg.showerror("Błąd", "Błąd serwera!")
            except ValueError: pass

        ctk.CTkButton(window, text="ZATWIERDŹ", fg_color="#00E676", text_color="black", command=zapisz).pack(pady=20)
