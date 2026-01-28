import customtkinter as ctk
import tkinter.messagebox as msg
from datetime import datetime
from api_service import wyslij_transakcje, dodaj_nowy_produkt_db, pobierz_historie
import json
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
HANDLED_FILE = os.path.join(project_root, "backend", "data", "wydane.json")

class WarehouseView(ctk.CTkFrame):
    def __init__(self, parent, app_controller):
        super().__init__(parent, fg_color="transparent")
        self.app = app_controller
        self.pack(fill="both", expand=True)
        
        self.wydane_ids = self.wczytaj_wydane()
        self.create_widgets()

    def wczytaj_wydane(self):
        if os.path.exists(HANDLED_FILE):
            try:
                with open(HANDLED_FILE, "r") as f:
                    return set(json.load(f))
            except: return set()
        return set()

    def zapisz_wydane(self):
        try:
            os.makedirs(os.path.dirname(HANDLED_FILE), exist_ok=True)
            with open(HANDLED_FILE, "w") as f:
                json.dump(list(self.wydane_ids), f)
        except Exception as e:
            print(f"Błąd zapisu: {e}")

    def create_widgets(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True)
        
        top_bar = ctk.CTkFrame(container, height=70, fg_color="#1a1a1a", corner_radius=10)
        top_bar.pack(fill="x", side="top", pady=(0, 10))
        
        ctk.CTkLabel(top_bar, text="MAGAZYN GŁÓWNY", font=("Impact", 24), text_color="#F2A900").pack(side="left", padx=20)
        ctk.CTkButton(top_bar, text="Wyjdź", command=self.app.pokaz_ekran_logowania, fg_color="#cf3030", width=100).pack(side="right", padx=20)
        
        grid = ctk.CTkFrame(container, fg_color="transparent")
        grid.pack(fill="both", expand=True)
        grid.grid_columnconfigure(0, weight=3)
        grid.grid_columnconfigure(1, weight=1)
        grid.grid_rowconfigure(0, weight=1)
        
        left = ctk.CTkFrame(grid, fg_color="transparent"); left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        header_left = ctk.CTkFrame(left, fg_color="transparent"); header_left.pack(fill="x", pady=5)
        ctk.CTkLabel(header_left, text="STAN ZASOBÓW", font=("Roboto", 16, "bold")).pack(side="left")
        ctk.CTkButton(header_left, text="+ PRZYJMIJ DOSTAWĘ", width=150, fg_color="#2cc985", text_color="black", 
                      command=self.pokaz_popup_dostawy).pack(side="right")
        
        self.inv_sc = ctk.CTkScrollableFrame(left, fg_color="#2b2b2b"); self.inv_sc.pack(fill="both", expand=True)
        
        right = ctk.CTkFrame(grid, fg_color="#111", corner_radius=10, border_color="#333", border_width=2); right.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(right, text="WYDANIA", font=("Impact", 18), text_color="#00E676").pack(pady=10)
        self.ord_sc = ctk.CTkScrollableFrame(right, fg_color="transparent"); self.ord_sc.pack(fill="both", expand=True)
        
        self.odswiez_magazyn()

    def odswiez_magazyn(self):
        for w in self.inv_sc.winfo_children(): w.destroy()
        
        self.app.odswiez_dane()
        sorted_products = sorted(self.app.produkty_db, key=lambda x: x['id'])
        for p in sorted_products: self.stworz_kafelek_magazynowy(self.inv_sc, p)
            
        for w in self.ord_sc.winfo_children(): w.destroy()
        
        historia = pobierz_historie()
        
        grouped_orders = {}
        
        if historia:
            for transakcja in historia:
                t_id = transakcja.get('trans_id') or transakcja.get('id')
                if t_id and t_id in self.wydane_ids: continue

                if transakcja.get('qty_change', 0) < 0:
                    user = transakcja.get('user_card_id', 'Unknown')
                    raw_time = transakcja.get('timestamp', '')
                    try:
                        dt = datetime.fromisoformat(raw_time)
                        time_key = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except: time_key = raw_time

                    group_key = (user, time_key)
                    if group_key not in grouped_orders: grouped_orders[group_key] = []
                    grouped_orders[group_key].append(transakcja)

        count = 0
        sorted_keys = sorted(grouped_orders.keys(), key=lambda x: x[1], reverse=True)
        for key in sorted_keys:
            self.stworz_karte_zbiorcza(self.ord_sc, grouped_orders[key])
            count += 1
        
        if count == 0: ctk.CTkLabel(self.ord_sc, text="Brak oczekujących\nwydań.", text_color="gray").pack(pady=50)

    def stworz_kafelek_magazynowy(self, parent, data):
        c = ctk.CTkFrame(parent, fg_color="#3a3a3a"); c.pack(fill="x", pady=5)
        header = ctk.CTkFrame(c, fg_color="transparent"); header.pack(fill="x", padx=15, pady=5)
        
        qty = data.get('qty', 0)
        name = data.get('name', 'Unknown')
        unit = data.get('unit', 'szt')
        max_cap = 100; ratio = qty / max_cap

        if ratio > 1.0: stat, col, bar_val = "NADMIAR", "#3B8ED0", 1.0
        elif ratio < 0.2: stat, col, bar_val = "KRYTYCZNY", "#FF1744", ratio
        elif ratio < 0.5: stat, col, bar_val = "UWAGA", "#FF9100", ratio
        else: stat, col, bar_val = "NORMA", "#00E676", ratio

        ctk.CTkLabel(header, text=name, font=("Roboto", 20, "bold")).pack(side="left")
        ctk.CTkLabel(header, text=stat, font=("Roboto", 12, "bold"), text_color=col).pack(side="right")
        
        bar = ctk.CTkProgressBar(c, progress_color=col); bar.set(bar_val); bar.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(c, text=f"Stan: {qty} {unit}", font=("Roboto", 14), text_color="#aaa").pack(fill="x", padx=15, pady=5)

    def stworz_karte_zbiorcza(self, parent, transactions_list):
        if not transactions_list: return
        first = transactions_list[0]
        user = first.get('user_card_id', 'Unknown')
        raw_time = first.get('timestamp', '')
        try:
            dt = datetime.fromisoformat(raw_time)
            czas_str = dt.strftime("%H:%M:%S")
        except: czas_str = raw_time

        card = ctk.CTkFrame(parent, fg_color="#1a1a1a", border_color="#00E676", border_width=1); card.pack(fill="x", pady=5)
        info = ctk.CTkFrame(card, fg_color="transparent"); info.pack(pady=5)
        ctk.CTkLabel(info, text=user, font=("Arial", 14, "bold"), text_color="white").pack()
        ctk.CTkLabel(info, text=czas_str, font=("Roboto", 10), text_color="gray").pack()
        
        items = ctk.CTkFrame(card, fg_color="transparent"); items.pack(pady=(0, 10), padx=10, fill="x")
        for item in transactions_list:
            p_name = item.get('product_name', '???'); p_qty = abs(item.get('qty_change', 0)); p_unit = item.get('unit', '')
            ctk.CTkLabel(items, text=f"• {p_name} x{p_qty} {p_unit}", font=("Roboto", 12)).pack(anchor="w")
        
        btn = ctk.CTkButton(card, text="WYDAJ", height=25, fg_color="#1F6AA5", hover_color="#144870",
                            command=lambda: self.zatwierdz_wydanie(card, transactions_list))
        btn.pack(fill="x", pady=5, padx=5)

    def zatwierdz_wydanie(self, card_widget, transactions_list):
        for t in transactions_list:
            t_id = t.get('trans_id') or t.get('id')
            if t_id: self.wydane_ids.add(t_id)
        self.zapisz_wydane()
        card_widget.destroy()
        if len(self.ord_sc.winfo_children()) == 0:
             ctk.CTkLabel(self.ord_sc, text="Brak oczekujących\nwydań.", text_color="gray").pack(pady=50)

    def pokaz_custom_popup(self, tytul, podtytul):
        popup = ctk.CTkToplevel(self)
        try:
            x = self.app.winfo_x() + (self.app.winfo_width()//2) - 250
            y = self.app.winfo_y() + (self.app.winfo_height()//2) - 175
        except: x, y = 100, 100
        popup.geometry(f"500x350+{x}+{y}")
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)

        popup.update_idletasks()
        popup.update()
        popup.grab_set()

        frame = ctk.CTkFrame(popup, fg_color="#111", border_width=4, border_color="#00E676")
        frame.pack(fill="both", expand=True)
        ctk.CTkLabel(frame, text="✔", font=("Arial", 80), text_color="#00E676").pack(pady=(40, 10))
        ctk.CTkLabel(frame, text=tytul, font=("Impact", 30), text_color="white").pack(pady=5)
        ctk.CTkLabel(frame, text=podtytul, font=("Roboto", 14), text_color="#aaa").pack(pady=10)
        ctk.CTkButton(frame, text="OK", font=("Roboto", 16, "bold"), fg_color="#00E676", text_color="black", height=50, width=200, command=popup.destroy).pack(pady=30)

    def pokaz_popup_dostawy(self):
        window = ctk.CTkToplevel(self)
        window.geometry("500x550")
        window.attributes("-topmost", True)

        window.update_idletasks()
        window.update()
        window.grab_set()

        
        tabs = ctk.CTkTabview(window)
        tabs.pack(fill="both", expand=True, padx=10, pady=10)
        
        tab_exist = tabs.add("DOSTAWA (ISTNIEJĄCY)")
        tab_new = tabs.add("REJESTRACJA NOWEGO")
        
        ctk.CTkLabel(tab_exist, text="PRZYJĘCIE DOSTAWY", font=("Impact", 18)).pack(pady=15)
        prod_names = [p['name'] for p in self.app.produkty_db]
        combo = ctk.CTkOptionMenu(tab_exist, values=prod_names, width=250); combo.pack(pady=10)
        entry = ctk.CTkEntry(tab_exist, placeholder_text="Ilość", width=250); entry.pack(pady=10)

        def zapisz_istniejacy():
            try:
                raw_qty = entry.get().replace(',', '.')
                ilosc = int(float(raw_qty))
                nazwa = combo.get()
                prod = next((p for p in self.app.produkty_db if p['name'] == nazwa), None)
                if prod:
                    if wyslij_transakcje(prod['id'], ilosc, self.app.user_card_id):
                        self.app.odswiez_dane()
                        self.odswiez_magazyn()
                        window.destroy()
                        self.pokaz_custom_popup("DOSTAWA PRZYJĘTA", f"Zaktualizowano stan: {nazwa}")
                    else: msg.showerror("Błąd", "Błąd komunikacji z serwerem!")
            except ValueError: pass

        ctk.CTkButton(tab_exist, text="ZATWIERDŹ", fg_color="#00E676", text_color="black", command=zapisz_istniejacy).pack(pady=20)

        f = ctk.CTkScrollableFrame(tab_new, fg_color="transparent")
        f.pack(fill="both", expand=True)
        
        ctk.CTkLabel(f, text="Nazwa produktu:").pack(anchor="w")
        e_name = ctk.CTkEntry(f, placeholder_text="np. Generator"); e_name.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(f, text="Kategoria (Wybierz z listy LUB KLIKNIJ I WPISZ WŁASNĄ):", font=("Roboto", 11, "bold"), text_color="#F2A900").pack(anchor="w")
        
        current_cats = set(p.get('category', 'Inne') for p in self.app.produkty_db)
        sorted_cats = sorted(list(current_cats))
        if not sorted_cats: sorted_cats = ["Inne"]
        
        e_cat = ctk.CTkComboBox(f, values=sorted_cats)
        e_cat.set("Inne")
        e_cat.pack(fill="x", pady=(0, 10))
        
        grid = ctk.CTkFrame(f, fg_color="transparent"); grid.pack(fill="x")
        ctk.CTkLabel(grid, text="Startowa ilość:").grid(row=0, column=0, padx=5, sticky="w")
        e_qty = ctk.CTkEntry(grid, width=100); e_qty.grid(row=1, column=0, padx=5)
        ctk.CTkLabel(grid, text="Jednostka:").grid(row=0, column=1, padx=5, sticky="w")
        e_unit = ctk.CTkEntry(grid, width=100, placeholder_text="szt"); e_unit.grid(row=1, column=1, padx=5)

        ctk.CTkLabel(f, text="Cena (Tokeny):").pack(anchor="w", pady=(10,0))
        e_price = ctk.CTkEntry(f); e_price.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(f, text="Limit darmowy / Max:").pack(anchor="w")
        grid2 = ctk.CTkFrame(f, fg_color="transparent"); grid2.pack(fill="x")
        e_free = ctk.CTkEntry(grid2, width=100, placeholder_text="Free"); e_free.pack(side="left", padx=5)
        e_max = ctk.CTkEntry(grid2, width=100, placeholder_text="Max"); e_max.pack(side="left", padx=5)

        def dodaj_nowy():
            try:
                nazwa = e_name.get().strip()
                kategoria = e_cat.get().strip()
                if not nazwa: return
                if not kategoria: kategoria = "Inne"

                raw_qty = e_qty.get().replace(',', '.')
                raw_price = e_price.get().replace(',', '.')
                raw_free = e_free.get().replace(',', '.')
                raw_max = e_max.get().replace(',', '.')

                ilosc = float(raw_qty) if raw_qty else 0.0
                cena = float(raw_price) if raw_price else 0.0
                l_free = int(float(raw_free)) if raw_free else 0
                l_max = int(float(raw_max)) if raw_max else 10

                sukces = dodaj_nowy_produkt_db(
                    nazwa=nazwa,
                    kategoria=kategoria,
                    ilosc=ilosc,
                    jednostka=e_unit.get(),
                    cena_extra=cena,
                    limit_free=l_free,
                    limit_max=l_max
                )
                if sukces:
                    self.app.odswiez_dane()
                    self.odswiez_magazyn()
                    window.destroy()
                    self.pokaz_custom_popup("SUKCES", "Utworzono nowy produkt!")
                else:
                    msg.showerror("Błąd", "Nie udało się utworzyć produktu.")
            except ValueError:
                msg.showerror("Błąd", "Sprawdź liczby!")

        ctk.CTkButton(f, text="+ UTWÓRZ W BAZIE", fg_color="#cf3030", hover_color="#8a1c1c", command=dodaj_nowy).pack(pady=20)
