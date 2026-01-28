import customtkinter as ctk
import tkinter.messagebox as msg
from api_service import pobierz_oferty, dodaj_oferte, usun_oferte

class ResidentView(ctk.CTkFrame):
    def __init__(self, parent, app_controller):
        super().__init__(parent, fg_color="transparent")
        self.app = app_controller
        
        self.cache_carts = {} 
        
        self.pack(fill="both", expand=True)
        self.create_widgets()

    def create_widgets(self):
        header = ctk.CTkFrame(self, height=80, fg_color="#1F6AA5", corner_radius=0)
        header.pack(fill="x", side="top")
        ctk.CTkLabel(header, text="👤", font=("Arial", 40)).pack(side="left", padx=20)
        
        user_info = ctk.CTkFrame(header, fg_color="transparent")
        user_info.pack(side="left", pady=10)
        ctk.CTkLabel(user_info, text=f"OBYWATEL: {self.app.aktualny_uzytkownik}", font=("Roboto", 18, "bold"), text_color="white").pack(anchor="w")
        self.lbl_saldo = ctk.CTkLabel(user_info, text=f"PORTFEL: {self.app.saldo_sesji} T", font=("Roboto", 14, "bold"), text_color="#FFD700")
        self.lbl_saldo.pack(anchor="w")

        ctk.CTkButton(header, text="WYLOGUJ", fg_color="#0d2b45", hover_color="#081a2b", 
                      command=self.app.pokaz_ekran_logowania, width=100).pack(side="right", padx=20)

        self.tab_view = ctk.CTkTabview(self, fg_color="transparent")
        self.tab_view.pack(fill="both", expand=True, padx=10, pady=10)
        self.tab_sklep = self.tab_view.add("MAGAZYN")
        self.tab_gielda = self.tab_view.add("GIEŁDA")
        
        # Lewa strona sklepu (Kategorie + Produkty)
        self.store_left_frame = ctk.CTkFrame(self.tab_sklep, fg_color="transparent")
        self.store_left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Prawa strona sklepu (Koszyk)
        self.store_right_frame = ctk.CTkFrame(self.tab_sklep, width=320, fg_color="#222222", corner_radius=15)
        self.store_right_frame.pack(side="right", fill="y")
        self.store_right_frame.pack_propagate(False)

        self.aktualna_kategoria = "WSZYSTKIE"
        
        self.prepare_ui_containers()
        self.zbuduj_sklep(force_rebuild=True)
        self.zbuduj_gielde()

    def prepare_ui_containers(self):
        self.filter_container = ctk.CTkFrame(self.store_left_frame, fg_color="transparent")
        self.filter_container.pack(fill="x", pady=(0, 10))
        
        self.products_scroll = ctk.CTkScrollableFrame(self.store_left_frame, label_text="ZASOBY")
        self.products_scroll.pack(fill="both", expand=True)
        self.products_scroll.grid_columnconfigure(0, weight=1)
        self.products_scroll.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.store_right_frame, text="PODSUMOWANIE", font=("Impact", 20), text_color="#F2A900").pack(pady=20)
        self.cart_items_frame = ctk.CTkScrollableFrame(self.store_right_frame, fg_color="transparent")
        self.cart_items_frame.pack(fill="both", expand=True, padx=10)
        
        footer = ctk.CTkFrame(self.store_right_frame, fg_color="transparent")
        footer.pack(side="bottom", fill="x", pady=20, padx=20)
        self.lbl_total_koszt = ctk.CTkLabel(footer, text="KOSZT: 0 T", font=("Roboto", 16, "bold"), text_color="#FFD700")
        self.lbl_total_koszt.pack(pady=5)
        self.btn_confirm = ctk.CTkButton(footer, text="ODBIERZ ZASOBY", height=60, font=("Roboto", 18, "bold"), 
                                         fg_color="#2cc985", text_color="black", state="disabled", 
                                         command=self.wyslij_zamowienie)
        self.btn_confirm.pack(fill="x")

    def zbuduj_sklep(self, force_rebuild=False):
        if not force_rebuild:
            self.quick_warehouse_update()
            return

        for w in self.filter_container.winfo_children(): w.destroy()
        for w in self.products_scroll.winfo_children(): w.destroy()
        self.cache_carts = {}

        unikalne_kategorie = set()
        for p in self.app.produkty_db:
            cat = p.get('category', 'Inne')
            if cat: unikalne_kategorie.add(cat)
        categories = ["WSZYSTKIE"] + sorted(list(unikalne_kategorie))

        if self.aktualna_kategoria not in categories: self.aktualna_kategoria = "WSZYSTKIE"

        seg = ctk.CTkSegmentedButton(self.filter_container, values=categories, 
                                     command=self.zmien_kategorie,
                                     selected_color="#1F6AA5", unselected_color="#333")
        seg.set(self.aktualna_kategoria)
        seg.pack(fill="x")

        self.products_scroll.configure(label_text=f"ZASOBY: {self.aktualna_kategoria}")

        produkty_do_wyswietlenia = []
        for produkt in self.app.produkty_db:
            kategoria_produktu = produkt.get('category', 'Inne')
            if self.aktualna_kategoria == "WSZYSTKIE" or kategoria_produktu == self.aktualna_kategoria:
                produkty_do_wyswietlenia.append(produkt)

        self._display_next_part(produkty_do_wyswietlenia, 0, 0, 0)

    def _display_next_part(self, lista_produktow, index, row, col):
        BATCH_SIZE = 6
        koniec = min(index + BATCH_SIZE, len(lista_produktow))

        for i in range(index, koniec):
            produkt = lista_produktow[i]
            self.stworz_karte_produktu(self.products_scroll, produkt, row, col)
            
            col += 1
            if col > 1:
                col = 0
                row += 1

        if koniec < len(lista_produktow):
            self.after(5, lambda: self._display_next_part(lista_produktow, koniec, row, col))
        else:
            self.odswiez_widok_koszyka()

    def zmien_kategorie(self, nowa_kat):
        self.aktualna_kategoria = nowa_kat
        self.zbuduj_sklep(force_rebuild=True)

    def stworz_karte_produktu(self, parent, data, row, col):
        pid = data['id']
        card = ctk.CTkFrame(parent, fg_color="#2b2b2b", border_width=2, border_color="#333333", width=250, height=340)
        card.grid(row=row, column=col, padx=10, pady=10)
        card.pack_propagate(False)

        header = ctk.CTkFrame(card, fg_color="transparent"); header.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(header, text=data.get('name', '???'), font=("Roboto", 16, "bold")).pack(side="left", anchor="w")
        price = data.get('extra_price', 0)
        col_p = "#FFD700" if price > 0 else "gray"
        ctk.CTkLabel(header, text=f"{price}T", font=("Roboto", 12, "bold"), text_color=col_p).pack(side="right")
        ctk.CTkLabel(card, text=data.get('category', '').upper(), font=("Arial", 10), text_color="#1F6AA5").pack(anchor="w", padx=10)

        cache_entry = {}

        # 1. Stan magazynowy i pasek
        bar_frame = ctk.CTkFrame(card, fg_color="transparent"); bar_frame.pack(fill="x", padx=20, pady=(10, 10))
        lbl_stan = ctk.CTkLabel(bar_frame, text="...", font=("Roboto", 10), text_color="gray")
        lbl_stan.pack(anchor="w")
        progress = ctk.CTkProgressBar(bar_frame, height=8, progress_color="#1F6AA5")
        progress.pack(fill="x", pady=5)
        
        cache_entry['lbl_stan'] = lbl_stan
        cache_entry['progress'] = progress

        # 2. Informacje o limitach (środek)
        info_frame = ctk.CTkFrame(card, fg_color="transparent", height=40); info_frame.pack_propagate(False); info_frame.pack(pady=5)
        info_center = ctk.CTkFrame(info_frame, fg_color="transparent"); info_center.place(relx=0.5, rely=0.5, anchor="center")
        
        lbl_info_1 = ctk.CTkLabel(info_center, text="", font=("Roboto", 11))
        lbl_info_1.pack()
        lbl_info_2 = ctk.CTkLabel(info_center, text="", font=("Roboto", 11))
        lbl_info_2.pack()

        cache_entry['lbl_info_1'] = lbl_info_1
        cache_entry['lbl_info_2'] = lbl_info_2

        # 3. Licznik wyboru (dół)
        control = ctk.CTkFrame(card, fg_color="#1a1a1a", corner_radius=20, width=160, height=50); control.pack(side="bottom", pady=20)
        
        lbl_qty_select = ctk.CTkLabel(control, text="0", font=("Roboto", 24, "bold"), text_color="white")
        lbl_qty_select.place(relx=0.5, rely=0.5, anchor="center")
        cache_entry['lbl_qty_select'] = lbl_qty_select

        ctk.CTkButton(control, text="-", width=40, height=30, fg_color="#444", hover_color="#333", 
                      command=lambda: self.zmien_ilosc(pid, -1)).place(relx=0.15, rely=0.5, anchor="w")
        ctk.CTkButton(control, text="+", width=40, height=30, fg_color="#1F6AA5", hover_color="#144870", 
                      command=lambda: self.zmien_ilosc(pid, 1)).place(relx=0.85, rely=0.5, anchor="e")

        self.cache_carts[pid] = cache_entry
        self.aktualizuj_jedna_karte(pid, data)

    def quick_warehouse_update(self):
        """Iteruje po cache i aktualizuje tylko teksty/wartości bez niszczenia UI"""
        for p in self.app.produkty_db:
            pid = p['id']
            if pid in self.cache_carts:
                self.aktualizuj_jedna_karte(pid, p)
        
        self.lbl_saldo.configure(text=f"PORTFEL: {self.app.saldo_sesji} T")
        self.odswiez_widok_koszyka()

    def aktualizuj_jedna_karte(self, pid, data):
        widgets = self.cache_carts.get(pid)
        if not widgets: return

        stock_qty = data.get('qty', 0)
        unit = data.get('unit', '')
        limit_free = data.get('limit_free', 0)
        limit_max = data.get('limit_max', 10)
        
        uzycie = self.app.uzycie_globalne.get(self.app.aktualny_uzytkownik, {})
        juz_pobrano = uzycie.get(pid, 0)
        
        pozostalo_free = max(0, limit_free - juz_pobrano)
        pozostalo_total = max(0, limit_max - juz_pobrano)
        platne_dostepne = max(0, pozostalo_total - pozostalo_free)

        # 1. Stan magazynowy
        widgets['lbl_stan'].configure(text=f"Stan: {stock_qty} {unit}")
        fill = stock_qty / 100
        widgets['progress'].set(1.0 if fill > 1.0 else fill)

        # 2. Limity
        if pozostalo_total == 0:
            widgets['lbl_info_1'].configure(text="WYKORZYSTANO LIMIT", text_color="red")
            widgets['lbl_info_2'].configure(text="")
        else:
            txt_free = f"Racja: {pozostalo_free}"
            col_free = "#00E676" if pozostalo_free > 0 else "gray"
            widgets['lbl_info_1'].configure(text=txt_free, text_color=col_free)

            txt_paid = f"Płatne: {platne_dostepne}"
            col_paid = "#FFD700" if platne_dostepne > 0 else "gray"
            widgets['lbl_info_2'].configure(text=txt_paid, text_color=col_paid)

        # 3. Licznik w koszyku
        w_koszyku = self.app.koszyk_uzytkownika.get(pid, 0)
        lbl = widgets['lbl_qty_select']
        lbl.configure(text=str(w_koszyku))
        
        # Kolor licznika
        darmowe_dostepne = max(0, limit_free - juz_pobrano)
        if w_koszyku > darmowe_dostepne: lbl.configure(text_color="#FFD700")
        elif w_koszyku > 0: lbl.configure(text_color="#00E676")
        else: lbl.configure(text_color="white")

    def zmien_ilosc(self, id_prod, delta):
        prod = next((p for p in self.app.produkty_db if p['id'] == id_prod), None)
        if not prod: return
        
        if delta > 0:
            limit_max = prod.get('limit_max', 999)
            w_koszyku = self.app.koszyk_uzytkownika.get(id_prod, 0)
            uzycie = self.app.uzycie_globalne.get(self.app.aktualny_uzytkownik, {})
            if w_koszyku >= max(0, limit_max - uzycie.get(id_prod, 0)): return
            if w_koszyku >= prod.get('qty', 0): return
            
        self.app.zmien_ilosc_w_koszyku(id_prod, delta)
        
        self.quick_warehouse_update()

    def odswiez_widok_koszyka(self):
        for w in self.cart_items_frame.winfo_children(): w.destroy()
        
        koszt_calkowity, suma_sztuk = 0, 0
        for pid, ilosc in self.app.koszyk_uzytkownika.items():
            if ilosc > 0:
                p = next((x for x in self.app.produkty_db if x['id'] == pid), None)
                if p:
                    suma_sztuk += ilosc
                    uzycie = self.app.uzycie_globalne.get(self.app.aktualny_uzytkownik, {}).get(pid, 0)
                    free_left = max(0, p.get('limit_free', 0) - uzycie)
                    w_free = min(ilosc, free_left)
                    w_paid = ilosc - w_free
                    koszt_pos = w_paid * p.get('extra_price', 0)
                    koszt_calkowity += koszt_pos
                    
                    row = ctk.CTkFrame(self.cart_items_frame, fg_color="transparent"); row.pack(fill="x", pady=2)
                    ctk.CTkLabel(row, text=p['name'], font=("Roboto", 12, "bold")).pack(side="left")
                    
                    if koszt_pos > 0:
                        ctk.CTkLabel(row, text=f"-{koszt_pos}T", font=("Roboto", 12, "bold"), text_color="#FFD700").pack(side="right")
                    else:
                        ctk.CTkLabel(row, text="FREE", font=("Roboto", 10, "bold"), text_color="#00E676").pack(side="right")
                    
                    detale = []
                    if w_free > 0: detale.append(f"{w_free} x FREE")
                    if w_paid > 0: detale.append(f"{w_paid} x PŁATNE")
                    ctk.CTkLabel(row, text=f" | ".join(detale), font=("Roboto", 10), text_color="gray").pack(side="left", padx=10)

        self.lbl_total_koszt.configure(text=f"KOSZT: {koszt_calkowity} T")
        state = "normal" if suma_sztuk > 0 else "disabled"
        self.btn_confirm.configure(state=state, fg_color="#2cc985" if suma_sztuk > 0 else "gray")

    def wyslij_zamowienie(self):
        if self.app.realizuj_zakup():
            self.pokaz_custom_popup("ZAKUP ZATWIERDZONY", "Pobrano środki. Zaktualizowano przydziały.")
            self.quick_warehouse_update()
        else:
            msg.showerror("Błąd", "Nie udało się zrealizować zamówienia lub brak środków.")

    def zbuduj_gielde(self):
        for w in self.tab_gielda.winfo_children(): w.destroy()
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
        oferty = pobierz_oferty()
        for i, of in enumerate(oferty):
            self.stworz_karte_oferty(self.offers_scroll, of, i//3, i%3)

    def stworz_karte_oferty(self, parent, oferta, row, col):
        card = ctk.CTkFrame(parent, fg_color="#333", border_color="gray", border_width=1)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(card, text=oferta['user'], font=("Roboto", 12, "bold"), text_color="#1F6AA5").pack(pady=5)
        exch = ctk.CTkFrame(card, fg_color="transparent"); exch.pack(pady=10)
        txt_daje = f"{oferta['daje_nazwa']} x{oferta['daje_ilosc']}"
        txt_szuka = f"{oferta['szuka_nazwa']} x{oferta['szuka_ilosc']}"
        ctk.CTkLabel(exch, text=txt_daje, font=("Arial", 14, "bold"), text_color="#ccc").pack(side="left", padx=5)
        ctk.CTkLabel(exch, text="➔", font=("Arial", 20), text_color="#F2A900").pack(side="left", padx=5)
        ctk.CTkLabel(exch, text=txt_szuka, font=("Arial", 14, "bold"), text_color="#ccc").pack(side="left", padx=5)
        
        czy_twoje = oferta['user'] == self.app.aktualny_uzytkownik
        btn_text = "TWOJE OGŁOSZENIE" if czy_twoje else "AKCEPTUJ"
        btn_color = "gray" if czy_twoje else "green"
        btn_state = "disabled" if czy_twoje else "normal"
        
        def akceptuj():
            if usun_oferte(oferta['id']):
                self.odswiez_gielde()
                self.pokaz_custom_popup("WYMIANA PRZYJĘTA", f"Udaj się do {oferta['user']} po odbiór.")
            else:
                msg.showerror("Błąd", "Nie udało się zaakceptować oferty.")
        ctk.CTkButton(card, text=btn_text, fg_color=btn_color, state=btn_state, height=30, command=akceptuj).pack(pady=10, padx=20, fill="x")

    def dodaj_oferte_popup(self):
        window = ctk.CTkToplevel(self)
        try:
            x = self.app.winfo_x() + (self.app.winfo_width() // 2) - 200
            y = self.app.winfo_y() + (self.app.winfo_height() // 2) - 200
        except: x, y = 100, 100
        window.geometry(f"400x400+{x}+{y}")
        window.attributes("-topmost", True)
        window.wait_visibility()
        window.grab_set()

        ctk.CTkLabel(window, text="KREATOR WYMIANY", font=("Impact", 20), text_color="#F2A900").pack(pady=15)
        prod_names = [p['name'] for p in self.app.produkty_db]
        
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
            if dodaj_oferte(self.app.aktualny_uzytkownik, c_daje.get(), d_val, c_szuka.get(), s_val):
                self.odswiez_gielde()
                window.destroy()
            else:
                msg.showerror("Błąd", "Błąd połączenia z serwerem")

        ctk.CTkButton(window, text="DODAJ OGŁOSZENIE", fg_color="#2cc985", text_color="black", command=save).pack(pady=20)

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