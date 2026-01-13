import customtkinter as ctk
import tkinter.messagebox as msg
import datetime
import requests


SERVER_URL = "http://127.0.0.1:8000"

# --- KONFIGURACJA WYGLĄDU ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class SystemDystrybucjiApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Ustawienia głównego okna
        self.title("System Dystrybucji Zasobów")
        self.geometry("1024x600")
        
        # --- BAZA PRODUKTÓW (Pobierana z serwera) ---
        self.produkty_db = self.pobierz_produkty_z_serwera()
        
        # --- DANE SYSTEMU ---
        self.historia_zamowien = [] 
        self.uzycie_globalne = {}   
        
        self.salda_uzytkownikow = {
            "USER_123": 50,
            "ADMIN_999": 999
        }
        
        self.oferty_gieldy = [
            {"user": "Jan_Kowalski", "daje": "Chleb x1", "szuka": "Woda 1.5L x2"},
            {"user": "Anna_Nowak", "daje": "Ryż 1kg x1", "szuka": "Tokeny x10"}
        ]

        self.koszyk_uzytkownika = {}
        self.aktualny_uzytkownik = None 
        self.saldo_sesji = 0 
        self.clock_loop = None 

        # Kontener główny
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Start
        self.pokaz_ekran_logowania()


    def pobierz_produkty_z_serwera(self):
        try:
            response = requests.get(f"{SERVER_URL}/api/products")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Błąd połączenia z serwerem: {e}")
            msg.showerror("Błąd Sieci", "Nie można połączyć się z serwerem (backend/main.py)!")
        return []

    def wyslij_transakcje_do_serwera(self, product_id, zmiana_ilosci):
        """Wysyła informację o zmianie stanu (kupno lub dostawa)"""
        payload = {
            "product_id": product_id,
            "qty_change": zmiana_ilosci,
            "user_card_id": self.aktualny_uzytkownik
        }
        try:
            response = requests.post(f"{SERVER_URL}/api/transaction", json=payload)
            return response.status_code == 200
        except:
            return False

    # =========================================================================
    # EKRAN 1: LOGOWANIE
    # =========================================================================
    def pokaz_ekran_logowania(self):
        self.wyczysc_ekran()
        bg_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        bg_frame.pack(fill="both", expand=True)

        top_bar = ctk.CTkFrame(bg_frame, height=40, fg_color="transparent")
        top_bar.pack(fill="x", padx=20, pady=10)
        self.lbl_clock = ctk.CTkLabel(top_bar, text="00:00:00", font=("Courier New", 20, "bold"), text_color="#00E676")
        self.lbl_clock.pack(side="right")
        self.aktualizuj_zegar() 
        ctk.CTkLabel(top_bar, text="SYSTEM v6.0 [CLIENT ONLINE]", font=("Courier New", 14), text_color="gray").pack(side="left")

        card = ctk.CTkFrame(bg_frame, width=500, height=400, corner_radius=20, border_width=2, border_color="#F2A900")
        card.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(card, text="⚡", font=("Arial", 60), text_color="#F2A900").pack(pady=(30, 0))
        ctk.CTkLabel(card, text="MAGAZYN ZASOBÓW", font=("Impact", 36)).pack(pady=5)
        ctk.CTkLabel(card, text="Terminal Autoryzacji", font=("Roboto", 14), text_color="gray").pack(pady=(0, 20))

        scan_area = ctk.CTkFrame(card, fg_color="#1a1a1a", corner_radius=10)
        scan_area.pack(pady=10, padx=40, fill="x")
        ctk.CTkLabel(scan_area, text=">>> OCZEKIWANIE NA TOKEN RFID <<<", font=("Courier New", 14, "bold"), text_color="#00E676").pack(pady=15)

        btns_frame = ctk.CTkFrame(card, fg_color="transparent")
        btns_frame.pack(pady=10)
        ctk.CTkButton(btns_frame, text="ID: MIESZKANIEC", command=lambda: self.zaloguj_uzytkownika("USER_123"), fg_color="#1F6AA5", width=180, height=50).pack(side="left", padx=10)
        ctk.CTkButton(btns_frame, text="ID: MAGAZYNIER", command=lambda: self.zaloguj_uzytkownika("ADMIN_999"), fg_color="#cf3030", width=180, height=50).pack(side="right", padx=10)
        
        footer = ctk.CTkFrame(bg_frame, height=30, fg_color="#111")
        footer.pack(side="bottom", fill="x", pady=10, padx=10)
        ctk.CTkLabel(footer, text=f"SERVER: {SERVER_URL} | STATUS: READY", font=("Consolas", 10), text_color="#555").pack()

    def aktualizuj_zegar(self):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        try:
            self.lbl_clock.configure(text=now)
            self.clock_loop = self.after(1000, self.aktualizuj_zegar)
        except: pass

    def zaloguj_uzytkownika(self, user_id):
        if self.clock_loop: self.after_cancel(self.clock_loop); self.clock_loop = None
        self.aktualny_uzytkownik = user_id
        
        self.produkty_db = self.pobierz_produkty_z_serwera()

        if user_id == "ADMIN_999":
            self.pokaz_ekran_magazynu()
        else:
            if user_id not in self.uzycie_globalne: self.uzycie_globalne[user_id] = {}
            if user_id not in self.salda_uzytkownikow: self.salda_uzytkownikow[user_id] = 50 
            self.saldo_sesji = self.salda_uzytkownikow[user_id]
            self.koszyk_uzytkownika = {}
            self.pokaz_ekran_mieszkanca()

    # =========================================================================
    # EKRAN 2: PANEL MIESZKAŃCA
    # =========================================================================
    def pokaz_ekran_mieszkanca(self):
        self.wyczysc_ekran()
        
        header = ctk.CTkFrame(self.main_container, height=80, fg_color="#1F6AA5", corner_radius=0)
        header.pack(fill="x", side="top")
        
        ctk.CTkLabel(header, text="👤", font=("Arial", 40)).pack(side="left", padx=20)
        user_info = ctk.CTkFrame(header, fg_color="transparent")
        user_info.pack(side="left", pady=10)
        ctk.CTkLabel(user_info, text=f"OBYWATEL: {self.aktualny_uzytkownik}", font=("Roboto", 18, "bold"), text_color="white").pack(anchor="w")
        self.lbl_saldo = ctk.CTkLabel(user_info, text=f"PORTFEL: {self.saldo_sesji} T", font=("Roboto", 14, "bold"), text_color="#FFD700")
        self.lbl_saldo.pack(anchor="w")

        ctk.CTkButton(header, text="WYLOGUJ", fg_color="#0d2b45", hover_color="#081a2b", command=self.pokaz_ekran_logowania, width=100).pack(side="right", padx=20)

        self.tab_view = ctk.CTkTabview(self.main_container, fg_color="transparent")
        self.tab_view.pack(fill="both", expand=True, padx=10, pady=10)
        self.tab_sklep = self.tab_view.add("MAGAZYN")
        self.tab_gielda = self.tab_view.add("GIEŁDA")

        self.zbuduj_zakladke_sklep()
        self.zbuduj_zakladke_gielda()

    def zbuduj_zakladke_sklep(self):
        products_scroll = ctk.CTkScrollableFrame(self.tab_sklep, label_text="DOSTĘPNE ZASOBY")
        products_scroll.pack(side="left", fill="both", expand=True, padx=(0, 10))
        products_scroll.grid_columnconfigure(0, weight=1); products_scroll.grid_columnconfigure(1, weight=1)

        for index, produkt in enumerate(self.produkty_db):
            row = index // 2; col = index % 2
            self.stworz_karte_produktu_kiosk(products_scroll, produkt, row, col)

        cart_panel = ctk.CTkFrame(self.tab_sklep, width=320, fg_color="#222222", corner_radius=15)
        cart_panel.pack(side="right", fill="y")
        
        ctk.CTkLabel(cart_panel, text="PODSUMOWANIE", font=("Impact", 20), text_color="#F2A900").pack(pady=20)

        footer_frame = ctk.CTkFrame(cart_panel, fg_color="transparent")
        footer_frame.pack(side="bottom", fill="x", pady=20, padx=20)
        
        self.lbl_total_koszt = ctk.CTkLabel(footer_frame, text="KOSZT: 0 T", font=("Roboto", 16, "bold"), text_color="#FFD700")
        self.lbl_total_koszt.pack(pady=5)
        
        self.btn_confirm = ctk.CTkButton(footer_frame, text="ODBIERZ ZASOBY", height=60, font=("Roboto", 18, "bold"), fg_color="#2cc985", text_color="black", state="disabled", command=self.wyslij_zamowienie)
        self.btn_confirm.pack(fill="x")

        self.cart_items_frame = ctk.CTkScrollableFrame(cart_panel, fg_color="transparent")
        self.cart_items_frame.pack(fill="both", expand=True, padx=10)
        self.odswiez_widok_koszyka()

    def stworz_karte_produktu_kiosk(self, parent, data, row, col):
        card = ctk.CTkFrame(parent, fg_color="#2b2b2b", border_width=2, border_color="#333333", width=250, height=340)
        card.grid(row=row, column=col, padx=10, pady=10)
        card.pack_propagate(False) 
        

        limit_free = data.get('limit_free', 0)
        limit_max = data.get('limit_max', 10)
        juz_pobrano_total = self.uzycie_globalne[self.aktualny_uzytkownik].get(data['id'], 0)
        
        pozostalo_free = max(0, limit_free - juz_pobrano_total)
        pozostalo_total = max(0, limit_max - juz_pobrano_total)
        platne_dostepne = max(0, pozostalo_total - pozostalo_free)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(header, text=data["name"], font=("Roboto", 18, "bold")).pack(side="left")
        ctk.CTkLabel(header, text=f"Extra: {data['extra_price']}T", font=("Roboto", 12), text_color="#FFD700").pack(side="right")
        
        icon_map = {"Woda": "💧", "Chleb": "🍞", "Ryż": "🍚", "Makaron": "🍝", "Leki": "💊"}
        icon = "📦"
        for key, val in icon_map.items():
            if key in data["name"]: icon = val
        ctk.CTkLabel(card, text=icon, font=("Arial", 60)).pack(pady=5)

        stan = data["qty"] / 100 
        color = "#1F6AA5" if stan > 0.2 else "#cf3030"
        bar_frame = ctk.CTkFrame(card, fg_color="transparent")
        bar_frame.pack(fill="x", padx=20)
        ctk.CTkLabel(bar_frame, text="Stan magazynu:", font=("Roboto", 10)).pack(anchor="w")
        progress = ctk.CTkProgressBar(bar_frame, height=10, progress_color=color)
        progress.set(stan)
        progress.pack(fill="x", pady=5)

        info_frame = ctk.CTkFrame(card, fg_color="transparent", height=40)
        info_frame.pack_propagate(False)
        info_frame.pack(pady=5)
        
        info_center = ctk.CTkFrame(info_frame, fg_color="transparent")
        info_center.place(relx=0.5, rely=0.5, anchor="center")
        
        if pozostalo_total == 0:
            ctk.CTkLabel(info_center, text="WYKORZYSTANO LIMIT", text_color="red", font=("Roboto", 12, "bold")).pack()
        else:
            txt_free = f"Racja: {pozostalo_free}"
            txt_paid = f"Płatne: {platne_dostepne}"
            ctk.CTkLabel(info_center, text=txt_free, text_color="#00E676" if pozostalo_free > 0 else "gray", font=("Roboto", 11)).pack()
            ctk.CTkLabel(info_center, text=txt_paid, text_color="#FFD700" if platne_dostepne > 0 else "gray", font=("Roboto", 11)).pack()

        control_frame = ctk.CTkFrame(card, fg_color="#1a1a1a", corner_radius=20, width=160, height=50)
        control_frame.pack_propagate(False)
        control_frame.pack(pady=10)
        
        ctk.CTkButton(control_frame, text="-", width=40, height=30, fg_color="#444", font=("Arial", 20),
                      command=lambda: self.zmien_ilosc(data['id'], -1)).place(relx=0.15, rely=0.5, anchor="w")
        
        lbl_qty = ctk.CTkLabel(control_frame, text="0", font=("Roboto", 24, "bold"), text_color="white")
        lbl_qty.place(relx=0.5, rely=0.5, anchor="center")
        
        data['label_ref'] = lbl_qty 
        
        ctk.CTkButton(control_frame, text="+", width=40, height=30, fg_color="#1F6AA5", font=("Arial", 20),
                      command=lambda: self.zmien_ilosc(data['id'], 1)).place(relx=0.85, rely=0.5, anchor="e")

    def zmien_ilosc(self, id_prod, delta):
        w_koszyku = self.koszyk_uzytkownika.get(id_prod, 0)
        if w_koszyku == 0 and delta < 0: return 

        produkt = next((item for item in self.produkty_db if item["id"] == id_prod), None)
        if not produkt: return
        
        max_magazyn = produkt['qty']
        limit_free = produkt['limit_free']
        limit_max = produkt['limit_max']
        juz_pobrano = self.uzycie_globalne[self.aktualny_uzytkownik].get(id_prod, 0)
        hard_cap = limit_max - juz_pobrano
        
        new_val = w_koszyku + delta
        if new_val < 0: new_val = 0
        if new_val > max_magazyn: return
        if new_val > hard_cap: return 

        temp = self.koszyk_uzytkownika.copy()
        temp[id_prod] = new_val
        if self.oblicz_koszt_calosci(temp) > self.saldo_sesji:
             if delta > 0: return 

        self.koszyk_uzytkownika[id_prod] = new_val
        
        if 'label_ref' in produkt:
            lbl = produkt['label_ref']
            lbl.configure(text=str(new_val))
            darmowe_dostepne = max(0, limit_free - juz_pobrano)
            if new_val > darmowe_dostepne: lbl.configure(text_color="#FFD700") 
            elif new_val > 0: lbl.configure(text_color="#00E676")
            else: lbl.configure(text_color="white")

        self.odswiez_widok_koszyka()

    def oblicz_koszt_calosci(self, koszyk_dict):
        total = 0
        for p in self.produkty_db:
            ilosc = koszyk_dict.get(p['id'], 0)
            if ilosc > 0:
                juz = self.uzycie_globalne[self.aktualny_uzytkownik].get(p['id'], 0)
                free = max(0, p['limit_free'] - juz)
                platne = max(0, ilosc - free)
                total += platne * p['extra_price']
        return total

    def odswiez_widok_koszyka(self):
        for w in self.cart_items_frame.winfo_children(): w.destroy()
        suma, koszt = 0, 0
        
        for p in self.produkty_db:
            ilosc = self.koszyk_uzytkownika.get(p['id'], 0)
            if ilosc > 0:
                suma += ilosc
                juz = self.uzycie_globalne[self.aktualny_uzytkownik].get(p['id'], 0)
                free = max(0, p['limit_free'] - juz)
                platne = max(0, ilosc - free)
                cena = platne * p['extra_price']
                koszt += cena
                
                row = ctk.CTkFrame(self.cart_items_frame, fg_color="transparent")
                row.pack(fill="x", pady=2)
                detale = ""
                if (ilosc - platne) > 0: detale += f"{ilosc-platne} - RACJA, "
                if platne > 0: detale += f"{platne} - PŁATNE"

                ctk.CTkLabel(row, text=f"{p['name']}", anchor="w", font=("Roboto", 12, "bold")).pack(side="left")
                txt_c = f"-{cena}T" if cena > 0 else "0T"
                col_c = "#FFD700" if cena > 0 else "#00E676"
                ctk.CTkLabel(row, text=txt_c, font=("Roboto", 12, "bold"), text_color=col_c).pack(side="right")
                ctk.CTkLabel(row, text=f"({detale})", font=("Roboto", 10), text_color="gray").pack(side="left", padx=5)
        
        self.lbl_total_koszt.configure(text=f"KOSZT: {koszt} T")
        state = "normal" if suma > 0 else "disabled"
        col = "#2cc985" if suma > 0 else "gray"
        self.btn_confirm.configure(state=state, fg_color=col)

    def wyslij_zamowienie(self):
        koszt = self.oblicz_koszt_calosci(self.koszyk_uzytkownika)
        if koszt > self.saldo_sesji: return

        # ### INTEGRACJA: Wysyłanie danych do serwera ###
        sukces_wszystkich = True
        items_list = []

        for p in self.produkty_db:
            ilosc_w_koszyku = self.koszyk_uzytkownika.get(p['id'], 0)
            if ilosc_w_koszyku > 0:
                # Wysyłamy do API informację o ZMNIEJSZENIU stanu (ujemna liczba)
                udalo_sie = self.wyslij_transakcje_do_serwera(p['id'], -ilosc_w_koszyku)
                if not udalo_sie:
                    sukces_wszystkich = False
                else:
                    items_list.append(f"{p['name']} x{ilosc_w_koszyku}")
                    # Aktualizujemy lokalnie limity
                    used = self.uzycie_globalne[self.aktualny_uzytkownik].get(p['id'], 0)
                    self.uzycie_globalne[self.aktualny_uzytkownik][p['id']] = used + ilosc_w_koszyku

        if sukces_wszystkich:
            self.salda_uzytkownikow[self.aktualny_uzytkownik] -= koszt
            self.saldo_sesji = self.salda_uzytkownikow[self.aktualny_uzytkownik]
            self.lbl_saldo.configure(text=f"PORTFEL: {self.saldo_sesji} T")
            
            # Pobieramy świeże dane z serwera po transakcji
            self.produkty_db = self.pobierz_produkty_z_serwera()
            self.zbuduj_zakladke_sklep() # Przebudowa sklepu
            
            self.pokaz_popup_sukcesu()
        else:
            msg.showerror("Błąd", "Część produktów nie mogła zostać wydana przez serwer.")

        self.koszyk_uzytkownika = {}

    def pokaz_custom_popup(self, tytul, podtytul):
        """Uniwersalna funkcja do wyświetlania okienek informacyjnych"""
        popup = ctk.CTkToplevel(self)
        x = self.winfo_x() + (self.winfo_width()//2) - 250
        y = self.winfo_y() + (self.winfo_height()//2) - 175
        popup.geometry(f"500x350+{x}+{y}")
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.grab_set()
        
        frame = ctk.CTkFrame(popup, fg_color="#111", border_width=4, border_color="#00E676")
        frame.pack(fill="both", expand=True)
        ctk.CTkLabel(frame, text="✔", font=("Arial", 80), text_color="#00E676").pack(pady=(40, 10))
        ctk.CTkLabel(frame, text=tytul, font=("Impact", 30), text_color="white").pack(pady=5)
        ctk.CTkLabel(frame, text=podtytul, font=("Roboto", 14), text_color="#aaa").pack(pady=10)
        
        ctk.CTkButton(frame, text="OK", font=("Roboto", 16, "bold"), fg_color="#00E676", text_color="black", 
                      height=50, width=200, command=popup.destroy).pack(pady=30)

    def pokaz_popup_sukcesu(self):
        self.pokaz_custom_popup("ZAKUP ZATWIERDZONY", "Pobrano środki. Zaktualizowano przydziały.")
        self.after(2000, self.pokaz_ekran_logowania) 

    # --- ZAKŁADKA GIEŁDY ---
    def zbuduj_zakladke_gielda(self):
        top_frame = ctk.CTkFrame(self.tab_gielda, height=60)
        top_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(top_frame, text="Wymieniaj zasoby z innymi!", font=("Roboto", 14)).pack(side="left", padx=20)
        ctk.CTkButton(top_frame, text="+ DODAJ OGŁOSZENIE", fg_color="#F2A900", text_color="black", 
                      command=self.dodaj_oferte_popup).pack(side="right", padx=20)
        self.offers_scroll = ctk.CTkScrollableFrame(self.tab_gielda, label_text="TABLICA OGŁOSZEŃ")
        self.offers_scroll.pack(fill="both", expand=True)
        self.offers_scroll.grid_columnconfigure(0, weight=1); self.offers_scroll.grid_columnconfigure(1, weight=1); self.offers_scroll.grid_columnconfigure(2, weight=1)
        self.odswiez_gielde()

    def odswiez_gielde(self):
        for w in self.offers_scroll.winfo_children(): w.destroy()
        for i, of in enumerate(self.oferty_gieldy): self.stworz_karte_oferty(self.offers_scroll, of, i//3, i%3)

    def stworz_karte_oferty(self, parent, oferta, row, col):
        card = ctk.CTkFrame(parent, fg_color="#333", border_color="gray", border_width=1)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(card, text=oferta['user'], font=("Roboto", 12, "bold"), text_color="#1F6AA5").pack(pady=5)
        exch = ctk.CTkFrame(card, fg_color="transparent"); exch.pack(pady=10)
        ctk.CTkLabel(exch, text=f"{oferta['daje']}", font=("Arial", 14, "bold"), text_color="#ccc").pack(side="left", padx=5)
        ctk.CTkLabel(exch, text="➔", font=("Arial", 20), text_color="#F2A900").pack(side="left", padx=5)
        ctk.CTkLabel(exch, text=f"{oferta['szuka']}", font=("Arial", 14, "bold"), text_color="#ccc").pack(side="left", padx=5)
        
        czy_twoje = oferta['user'] == self.aktualny_uzytkownik
        btn_text = "TWOJE OGŁOSZENIE" if czy_twoje else "AKCEPTUJ"
        btn_color = "gray" if czy_twoje else "green"
        btn_state = "disabled" if czy_twoje else "normal"
        
        def akceptuj():
            if oferta in self.oferty_gieldy:
                self.oferty_gieldy.remove(oferta)
                self.odswiez_gielde()
                self.pokaz_custom_popup("WYMIANA PRZYJĘTA", f"Udaj się do punktu wymiany.\nKontrahent: {oferta['user']}")

        ctk.CTkButton(card, text=btn_text, fg_color=btn_color, state=btn_state, height=30, 
                      command=akceptuj).pack(pady=10, padx=20, fill="x")

    def dodaj_oferte_popup(self):
        window = ctk.CTkToplevel(self)
        x = self.winfo_x() + (self.winfo_width() // 2) - 200
        y = self.winfo_y() + (self.winfo_height() // 2) - 200
        window.geometry(f"400x400+{x}+{y}")
        window.attributes("-topmost", True)
        window.grab_set()

        ctk.CTkLabel(window, text="KREATOR WYMIANY", font=("Impact", 20), text_color="#F2A900").pack(pady=15)
        
        prod_names = [p['name'] for p in self.produkty_db]
        
        frame_daje = ctk.CTkFrame(window, fg_color="transparent"); frame_daje.pack(pady=5)
        ctk.CTkLabel(frame_daje, text="ODDAM:", width=60).pack(side="left")
        c_daje = ctk.CTkOptionMenu(frame_daje, values=prod_names); c_daje.pack(side="left", padx=5)
        e_daje = ctk.CTkEntry(frame_daje, width=50, placeholder_text="Ile"); e_daje.pack(side="left")

        frame_szuka = ctk.CTkFrame(window, fg_color="transparent"); frame_szuka.pack(pady=5)
        ctk.CTkLabel(frame_szuka, text="SZUKAM:", width=60).pack(side="left")
        c_szuka = ctk.CTkOptionMenu(frame_szuka, values=prod_names + ["Tokeny"]); c_szuka.pack(side="left", padx=5)
        e_szuka = ctk.CTkEntry(frame_szuka, width=50, placeholder_text="Ile"); e_szuka.pack(side="left")

        def save():
            d_val = e_daje.get() if e_daje.get() else "1"
            s_val = e_szuka.get() if e_szuka.get() else "1"
            txt_daje = f"{c_daje.get()} x{d_val}"
            txt_szuka = f"{c_szuka.get()} x{s_val}"
            self.oferty_gieldy.insert(0, {"user": self.aktualny_uzytkownik, "daje": txt_daje, "szuka": txt_szuka})
            self.odswiez_gielde()
            
            self.focus_set()
            window.grab_release()
            window.destroy()

        ctk.CTkButton(window, text="DODAJ OGŁOSZENIE", fg_color="#2cc985", text_color="black", command=save).pack(pady=20)

    # =========================================================================
    # EKRAN 3: MAGAZYNIER
    # =========================================================================
    def pokaz_ekran_magazynu(self):
        self.wyczysc_ekran()
        container = ctk.CTkFrame(self.main_container, fg_color="transparent"); container.pack(fill="both", expand=True)
        top_bar = ctk.CTkFrame(container, height=70, fg_color="#1a1a1a", corner_radius=10); top_bar.pack(fill="x", side="top", pady=(0, 10))
        ctk.CTkLabel(top_bar, text="MAGAZYN GŁÓWNY", font=("Impact", 24), text_color="#F2A900").pack(side="left", padx=20)
        ctk.CTkButton(top_bar, text="Wyjdź", command=self.pokaz_ekran_logowania, fg_color="#cf3030").pack(side="right", padx=20)
        
        grid = ctk.CTkFrame(container, fg_color="transparent"); grid.pack(fill="both", expand=True)
        grid.grid_columnconfigure(0, weight=8); grid.grid_columnconfigure(1, weight=2); grid.grid_rowconfigure(0, weight=1)
        
        left = ctk.CTkFrame(grid, fg_color="transparent"); left.grid(row=0, column=0, sticky="nsew", padx=(0,10))
        
        # --- BUTTON DODAWANIA DOSTAWY ---
        header_left = ctk.CTkFrame(left, fg_color="transparent")
        header_left.pack(fill="x", pady=5)
        ctk.CTkLabel(header_left, text="STAN ZASOBÓW", font=("Roboto", 16, "bold")).pack(side="left")
        ctk.CTkButton(header_left, text="+ PRZYJMIJ DOSTAWĘ", width=150, fg_color="#2cc985", text_color="black", 
                      command=self.pokaz_popup_dostawy).pack(side="right")

        self.inv_sc = ctk.CTkScrollableFrame(left, fg_color="#2b2b2b"); self.inv_sc.pack(fill="both", expand=True)
        
        right = ctk.CTkFrame(grid, fg_color="#111", corner_radius=10, border_color="#333", border_width=2); right.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(right, text="WYDANIA", font=("Impact", 18), text_color="#00E676").pack(pady=10)
        self.ord_sc = ctk.CTkScrollableFrame(right, fg_color="transparent"); self.ord_sc.pack(fill="both", expand=True)
        self.odswiez_magazyn()

    def pokaz_popup_dostawy(self):
        window = ctk.CTkToplevel(self)
        x = self.winfo_x() + (self.winfo_width() // 2) - 150
        y = self.winfo_y() + (self.winfo_height() // 2) - 150
        window.geometry(f"300x250+{x}+{y}")
        window.attributes("-topmost", True)
        window.grab_set()

        ctk.CTkLabel(window, text="PRZYJĘCIE DOSTAWY", font=("Impact", 18)).pack(pady=15)
        
        prod_names = [p['name'] for p in self.produkty_db]
        combo_prod = ctk.CTkOptionMenu(window, values=prod_names)
        combo_prod.pack(pady=10)
        
        entry_qty = ctk.CTkEntry(window, placeholder_text="Ilość")
        entry_qty.pack(pady=10)

        def zapisz():
            try:
                ilosc = int(entry_qty.get())
                nazwa = combo_prod.get()
                
                # Znajdź produkt, żeby pobrać jego ID
                prod = next((p for p in self.produkty_db if p['name'] == nazwa), None)
                
                if prod:
                    # ### INTEGRACJA: Wysyłamy +ilosc do serwera ###
                    sukces = self.wyslij_transakcje_do_serwera(prod['id'], ilosc)
                    
                    if sukces:
                        self.produkty_db = self.pobierz_produkty_z_serwera() # Odśwież dane
                        self.odswiez_magazyn()
                        
                        self.focus_set()
                        window.grab_release()
                        window.destroy()
                        self.pokaz_custom_popup("DOSTAWA PRZYJĘTA", f"Zaktualizowano stan: {nazwa}")
                    else:
                        msg.showerror("Błąd", "Błąd zapisu na serwerze!")
            except ValueError:
                pass

        ctk.CTkButton(window, text="ZATWIERDŹ", fg_color="#00E676", text_color="black", command=zapisz).pack(pady=20)

    def odswiez_magazyn(self):
        for w in self.inv_sc.winfo_children(): w.destroy()
        for p in self.produkty_db: self.stworz_kafelek_magazynowy(self.inv_sc, p)
        for w in self.ord_sc.winfo_children(): w.destroy()
        if not self.historia_zamowien: ctk.CTkLabel(self.ord_sc, text="Brak zamówień.", text_color="gray").pack(pady=50)
        else:
            for z in self.historia_zamowien: self.stworz_karte_zamowienia(self.ord_sc, z)

    def zrealizuj_zamowienie(self, z):
        if z in self.historia_zamowien: self.historia_zamowien.remove(z); self.odswiez_magazyn()

    def stworz_kafelek_magazynowy(self, p, d):
        c = ctk.CTkFrame(p, fg_color="#3a3a3a"); c.pack(fill="x", pady=5)
        header = ctk.CTkFrame(c, fg_color="transparent"); header.pack(fill="x", padx=15, pady=5)
        
        # Logika pasków (Overflow)
        ratio = d["qty"] / d["max"]
        if ratio > 1.0:
            stat = "NADMIAR"; col = "#3B8ED0"; bar_val = 1.0
        elif ratio < 0.2:
            stat = "KRYTYCZNY"; col = "#FF1744"; bar_val = ratio
        elif ratio < 0.5:
            stat = "UWAGA"; col = "#FF9100"; bar_val = ratio
        else:
            stat = "NORMA"; col = "#00E676"; bar_val = ratio

        ctk.CTkLabel(header, text=d["name"], font=("Roboto", 20, "bold")).pack(side="left")
        ctk.CTkLabel(header, text=stat, font=("Roboto", 12, "bold"), text_color=col).pack(side="right")
        
        bar = ctk.CTkProgressBar(c, progress_color=col)
        bar.set(bar_val)
        bar.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(c, text=f"Stan: {d['qty']} / {d['max']} {d['unit']}", font=("Roboto", 14), text_color="#aaa").pack(fill="x", padx=15, pady=5)

    def stworz_karte_zamowienia(self, p, d):
        c = ctk.CTkFrame(p, fg_color="#1a1a1a", border_color="#00E676", border_width=1); c.pack(fill="x", pady=5)
        ctk.CTkLabel(c, text=d['user'], font=("Arial", 14, "bold"), text_color="white").pack()
        ctk.CTkLabel(c, text=d['czas'], font=("Roboto", 10), text_color="gray").pack()
        for i in d['produkty']: ctk.CTkLabel(c, text=f"• {i}").pack()
        ctk.CTkButton(c, text="WYDAJ", height=25, command=lambda: self.zrealizuj_zamowienie(d)).pack(fill="x", pady=5)

    def wyczysc_ekran(self):
        for widget in self.main_container.winfo_children(): widget.destroy()

if __name__ == "__main__":
    app = SystemDystrybucjiApp()
    app.mainloop()