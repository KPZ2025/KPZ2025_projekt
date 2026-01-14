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
        
        user_info = ctk.CTkFrame(header, fg_color="transparent"); user_info.pack(side="left", pady=10)
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
        products_scroll = ctk.CTkScrollableFrame(self.tab_sklep, label_text="DOSTĘPNE ZASOBY")
        products_scroll.pack(side="left", fill="both", expand=True, padx=(0, 10))
        products_scroll.grid_columnconfigure(0, weight=1); products_scroll.grid_columnconfigure(1, weight=1)

        for index, produkt in enumerate(self.app.produkty_db):
            row = index // 2; col = index % 2
            self.stworz_karte_produktu(products_scroll, produkt, row, col)

        cart_panel = ctk.CTkFrame(self.tab_sklep, width=320, fg_color="#222222", corner_radius=15)
        cart_panel.pack(side="right", fill="y")
        ctk.CTkLabel(cart_panel, text="KOSZYK", font=("Impact", 20), text_color="#F2A900").pack(pady=20)
        
        self.cart_items_frame = ctk.CTkScrollableFrame(cart_panel, fg_color="transparent")
        self.cart_items_frame.pack(fill="both", expand=True, padx=10)
        
        footer = ctk.CTkFrame(cart_panel, fg_color="transparent"); footer.pack(side="bottom", fill="x", pady=20, padx=20)
        self.lbl_total_koszt = ctk.CTkLabel(footer, text="KOSZT: 0 T", font=("Roboto", 16, "bold"), text_color="#FFD700"); self.lbl_total_koszt.pack(pady=5)
        self.btn_confirm = ctk.CTkButton(footer, text="ODBIERZ", height=60, font=("Roboto", 18, "bold"), fg_color="#2cc985", text_color="black", state="disabled", command=self.wyslij_zamowienie); self.btn_confirm.pack(fill="x")
        
        self.odswiez_widok_koszyka()

    def stworz_karte_produktu(self, parent, data, row, col):
        card = ctk.CTkFrame(parent, fg_color="#2b2b2b", border_width=2, border_color="#333333", width=250, height=340)
        card.grid(row=row, column=col, padx=10, pady=10); card.pack_propagate(False)
        
        limit_free = data.get('limit_free', 0)
        limit_max = data.get('limit_max', 10)
        extra_price = data.get('extra_price', 0)
        name = data.get('name', '???')
        
        ctk.CTkLabel(card, text=name, font=("Roboto", 18, "bold")).pack(pady=5)
        ctk.CTkLabel(card, text=f"Extra: {extra_price} T", font=("Roboto", 12), text_color="#FFD700").pack()

        control = ctk.CTkFrame(card, fg_color="#1a1a1a", corner_radius=20, width=160, height=50); control.pack(side="bottom", pady=20)
        lbl_qty = ctk.CTkLabel(control, text="0", font=("Roboto", 24, "bold"), text_color="white"); lbl_qty.place(relx=0.5, rely=0.5, anchor="center")
        
        data['label_ref'] = lbl_qty 

        ctk.CTkButton(control, text="-", width=40, command=lambda: self.zmien_ilosc(data['id'], -1)).place(relx=0.15, rely=0.5, anchor="w")
        ctk.CTkButton(control, text="+", width=40, command=lambda: self.zmien_ilosc(data['id'], 1)).place(relx=0.85, rely=0.5, anchor="e")

    def zmien_ilosc(self, id_prod, delta):
        self.app.zmien_ilosc_w_koszyku(id_prod, delta)
        self.odswiez_widok_koszyka()

    def odswiez_widok_koszyka(self):
        for w in self.cart_items_frame.winfo_children(): w.destroy()
        
        koszt = self.app.oblicz_koszt_calosci()
        self.lbl_total_koszt.configure(text=f"KOSZT: {koszt} T")
        
        suma_sztuk = 0
        for pid, ilosc in self.app.koszyk_uzytkownika.items():
            if ilosc > 0:
                suma_sztuk += ilosc
                p = next((x for x in self.app.produkty_db if x['id'] == pid), None)
                if p:
                    row = ctk.CTkFrame(self.cart_items_frame, fg_color="transparent")
                    row.pack(fill="x", pady=2)
                    ctk.CTkLabel(row, text=f"{p['name']} x{ilosc}", font=("Roboto", 12)).pack(side="left")

        state = "normal" if suma_sztuk > 0 else "disabled"
        self.btn_confirm.configure(state=state, fg_color="#2cc985" if suma_sztuk > 0 else "gray")
        
        for p in self.app.produkty_db:
            if 'label_ref' in p:
                qty = self.app.koszyk_uzytkownika.get(p['id'], 0)
                p['label_ref'].configure(text=str(qty), text_color="#00E676" if qty > 0 else "white")

    def wyslij_zamowienie(self):
        if self.app.realizuj_zakup():
            self.app.pokaz_custom_popup("SUKCES", "Zakup udany!")
            self.app.odswiez_dane()
            self.zbuduj_sklep()
        else:
            msg.showerror("Błąd", "Nie udało się zrealizować zamówienia.")

    def zbuduj_gielde(self):
        ctk.CTkLabel(self.tab_gielda, text="GIEŁDA ZASOBÓW (W BUDOWIE)", font=("Impact", 30)).pack(pady=50)
