import customtkinter as ctk
import tkinter.messagebox as msg

class ResidentView(ctk.CTkFrame):
    def __init__(self, parent, app_controller):
        super().__init__(parent, fg_color="transparent")
        self.app = app_controller
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

        self.zbuduj_sklep()
        self.zbuduj_gielde()

    def zbuduj_sklep(self):
        for widget in self.tab_sklep.winfo_children():
            widget.destroy()

        products_scroll = ctk.CTkScrollableFrame(self.tab_sklep, label_text="DOSTĘPNE ZASOBY")
        products_scroll.pack(side="left", fill="both", expand=True, padx=(0, 10))
        products_scroll.grid_columnconfigure(0, weight=1)
        products_scroll.grid_columnconfigure(1, weight=1)

        for index, produkt in enumerate(self.app.produkty_db):
            row = index // 2
            col = index % 2
            self.stworz_karte_produktu(products_scroll, produkt, row, col)

        cart_panel = ctk.CTkFrame(self.tab_sklep, width=320, fg_color="#222222", corner_radius=15)
        cart_panel.pack(side="right", fill="y")
        
        ctk.CTkLabel(cart_panel, text="PODSUMOWANIE", font=("Impact", 20), text_color="#F2A900").pack(pady=20)
        
        self.cart_items_frame = ctk.CTkScrollableFrame(cart_panel, fg_color="transparent")
        self.cart_items_frame.pack(fill="both", expand=True, padx=10)
        
        footer = ctk.CTkFrame(cart_panel, fg_color="transparent")
        footer.pack(side="bottom", fill="x", pady=20, padx=20)
        
        self.lbl_total_koszt = ctk.CTkLabel(footer, text="KOSZT: 0 T", font=("Roboto", 16, "bold"), text_color="#FFD700")
        self.lbl_total_koszt.pack(pady=5)
        
        self.btn_confirm = ctk.CTkButton(footer, text="ODBIERZ ZASOBY", height=60, font=("Roboto", 18, "bold"), 
                                         fg_color="#2cc985", text_color="black", state="disabled", 
                                         command=self.wyslij_zamowienie)
        self.btn_confirm.pack(fill="x")
        
        self.odswiez_widok_koszyka()

    def stworz_karte_produktu(self, parent, data, row, col):
        card = ctk.CTkFrame(parent, fg_color="#2b2b2b", border_width=2, border_color="#333333", width=250, height=340)
        card.grid(row=row, column=col, padx=10, pady=10)
        card.pack_propagate(False)
        
        limit_free = data.get('limit_free', 0)
        limit_max = data.get('limit_max', 10)
        extra_price = data.get('extra_price', 0)
        name = data.get('name', '???')
        stock_qty = data.get('qty', 0)
        unit = data.get('unit', '')
        
        uzycie_uzytkownika = self.app.uzycie_globalne.get(self.app.aktualny_uzytkownik, {})
        juz_pobrano_total = uzycie_uzytkownika.get(data['id'], 0)
        
        pozostalo_free = max(0, limit_free - juz_pobrano_total)
        pozostalo_total = max(0, limit_max - juz_pobrano_total)
        platne_dostepne = max(0, pozostalo_total - pozostalo_free)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(header, text=name, font=("Roboto", 18, "bold")).pack(side="left")
        ctk.CTkLabel(header, text=f"Extra: {extra_price}T", font=("Roboto", 12), text_color="#FFD700").pack(side="right")

        bar_frame = ctk.CTkFrame(card, fg_color="transparent")
        bar_frame.pack(fill="x", padx=20, pady=(15, 15))
        
        ctk.CTkLabel(bar_frame, text=f"Stan magazynu ({stock_qty} {unit}):", font=("Roboto", 10), text_color="gray").pack(anchor="w")
        progress = ctk.CTkProgressBar(bar_frame, height=10, progress_color="#1F6AA5")
        
        fill_level = stock_qty / 100
        if fill_level > 1.0: fill_level = 1.0
        progress.set(fill_level)
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

        control = ctk.CTkFrame(card, fg_color="#1a1a1a", corner_radius=20, width=160, height=50)
        control.pack(side="bottom", pady=20)
        
        lbl_qty = ctk.CTkLabel(control, text="0", font=("Roboto", 24, "bold"), text_color="white")
        lbl_qty.place(relx=0.5, rely=0.5, anchor="center")
        
        data['label_ref'] = lbl_qty 

        ctk.CTkButton(control, text="-", width=40, height=30, fg_color="#444", hover_color="#333", font=("Arial", 20),
                      command=lambda: self.zmien_ilosc(data['id'], -1)).place(relx=0.15, rely=0.5, anchor="w")
        ctk.CTkButton(control, text="+", width=40, height=30, fg_color="#1F6AA5", hover_color="#144870", font=("Arial", 20),
                      command=lambda: self.zmien_ilosc(data['id'], 1)).place(relx=0.85, rely=0.5, anchor="e")

    def zmien_ilosc(self, id_prod, delta):
        prod = next((p for p in self.app.produkty_db if p['id'] == id_prod), None)
        if not prod: return

        if delta > 0:
            limit_max = prod.get('limit_max', 999)
            w_koszyku = self.app.koszyk_uzytkownika.get(id_prod, 0)
            uzycie_uzytkownika = self.app.uzycie_globalne.get(self.app.aktualny_uzytkownik, {})
            juz_kupiono = uzycie_uzytkownika.get(id_prod, 0)
            pozostalo_limitu = max(0, limit_max - juz_kupiono)

            if w_koszyku >= pozostalo_limitu: return
            if w_koszyku >= prod.get('qty', 0): return

        self.app.zmien_ilosc_w_koszyku(id_prod, delta)
        self.odswiez_widok_koszyka()

    def odswiez_widok_koszyka(self):
        for w in self.cart_items_frame.winfo_children():
            w.destroy()
        
        koszt_calkowity = 0
        suma_sztuk = 0
        
        for pid, ilosc in self.app.koszyk_uzytkownika.items():
            if ilosc > 0:
                p = next((x for x in self.app.produkty_db if x['id'] == pid), None)
                if p:
                    suma_sztuk += ilosc
                    uzycie_uzytkownika = self.app.uzycie_globalne.get(self.app.aktualny_uzytkownik, {})
                    juz_pobrano = uzycie_uzytkownika.get(pid, 0)
                    limit_free = p.get('limit_free', 0)
                    
                    free_left = max(0, limit_free - juz_pobrano)
                    w_tej_transakcji_free = min(ilosc, free_left)
                    w_tej_transakcji_platne = ilosc - w_tej_transakcji_free
                    
                    cena_jednostkowa = p.get('extra_price', 0)
                    koszt_pozycji = w_tej_transakcji_platne * cena_jednostkowa
                    koszt_calkowity += koszt_pozycji
                    
                    row = ctk.CTkFrame(self.cart_items_frame, fg_color="transparent")
                    row.pack(fill="x", pady=5)
                    
                    ctk.CTkLabel(row, text=f"{p['name']}", anchor="w", font=("Roboto", 12, "bold")).pack(side="left")
                    
                    txt_c = f"-{koszt_pozycji}T" if koszt_pozycji > 0 else "0T"
                    col_c = "#FFD700" if koszt_pozycji > 0 else "#00E676"
                    ctk.CTkLabel(row, text=txt_c, font=("Roboto", 12, "bold"), text_color=col_c).pack(side="right")
                    
                    detale = []
                    if w_tej_transakcji_free > 0: detale.append(f"{w_tej_transakcji_free} - RACJA")
                    if w_tej_transakcji_platne > 0: detale.append(f"{w_tej_transakcji_platne} - PŁATNE")
                    detale_txt = f"({', '.join(detale)})"
                    
                    ctk.CTkLabel(row, text=detale_txt, font=("Roboto", 10), text_color="gray").pack(side="left", padx=5)

        self.lbl_total_koszt.configure(text=f"KOSZT: {koszt_calkowity} T")
        
        state = "normal" if suma_sztuk > 0 else "disabled"
        col = "#2cc985" if suma_sztuk > 0 else "gray"
        self.btn_confirm.configure(state=state, fg_color=col)
        
        for p in self.app.produkty_db:
            if 'label_ref' in p:
                qty = self.app.koszyk_uzytkownika.get(p['id'], 0)
                p['label_ref'].configure(text=str(qty))
                
                uzycie = self.app.uzycie_globalne.get(self.app.aktualny_uzytkownik, {}).get(p['id'], 0)
                darmowe_dostepne = max(0, p.get('limit_free', 0) - uzycie)
                
                if qty > darmowe_dostepne: p['label_ref'].configure(text_color="#FFD700")
                elif qty > 0: p['label_ref'].configure(text_color="#00E676")
                else: p['label_ref'].configure(text_color="white")

    def wyslij_zamowienie(self):
        if self.app.realizuj_zakup():
            # --- ZMIANA: Używamy lokalnego, ładnego okienka ---
            self.pokaz_custom_popup("ZAKUP ZATWIERDZONY", "Pobrano środki. Zaktualizowano przydziały.")
            
            self.app.odswiez_dane()
            self.zbuduj_sklep()
        else:
            msg.showerror("Błąd", "Nie udało się zrealizować zamówienia.")

    # --- NOWA FUNKCJA (ZE STAREGO KODU) ---
    def pokaz_custom_popup(self, tytul, podtytul):
        """Wyświetla okienko sukcesu z dużym zielonym ptaszkiem"""
        popup = ctk.CTkToplevel(self)
        
        # Centrowanie
        try:
            x = self.app.winfo_x() + (self.app.winfo_width()//2) - 250
            y = self.app.winfo_y() + (self.app.winfo_height()//2) - 175
        except: x, y = 100, 100
            
        popup.geometry(f"500x350+{x}+{y}")
        popup.overrideredirect(True) # Bez paska tytułu
        popup.attributes("-topmost", True)
        popup.grab_set()
        
        frame = ctk.CTkFrame(popup, fg_color="#111", border_width=4, border_color="#00E676")
        frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(frame, text="✔", font=("Arial", 80), text_color="#00E676").pack(pady=(40, 10))
        ctk.CTkLabel(frame, text=tytul, font=("Impact", 30), text_color="white").pack(pady=5)
        ctk.CTkLabel(frame, text=podtytul, font=("Roboto", 14), text_color="#aaa").pack(pady=10)
        
        ctk.CTkButton(frame, text="OK", font=("Roboto", 16, "bold"), fg_color="#00E676", text_color="black", 
                      height=50, width=200, command=popup.destroy).pack(pady=30)

    def zbuduj_gielde(self):
        ctk.CTkLabel(self.tab_gielda, text="GIEŁDA ZASOBÓW (W BUDOWIE)", font=("Impact", 30)).pack(pady=50)
