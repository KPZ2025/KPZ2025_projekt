import customtkinter as ctk
import datetime
import requests

API_RFID = "http://127.0.0.1:8000/api/rfid"

class LoginView(ctk.CTkFrame):
    def __init__(self, parent, app_controller):
        super().__init__(parent, fg_color="transparent")
        self.app = app_controller
        self.pack(fill="both", expand=True)
        self.create_widgets()
        self.sprawdz_rfid()
        
    def create_widgets(self):
        bg_frame = ctk.CTkFrame(self, fg_color="transparent")
        bg_frame.pack(fill="both", expand=True)

        top_bar = ctk.CTkFrame(bg_frame, height=40, fg_color="transparent")
        top_bar.pack(fill="x", padx=20, pady=10)
        self.lbl_clock = ctk.CTkLabel(top_bar, text="00:00:00", font=("Courier New", 20, "bold"), text_color="#00E676")
        self.lbl_clock.pack(side="right")
        self.aktualizuj_zegar()
        ctk.CTkLabel(top_bar, text="SYSTEM v7.0 (RFID READY)", font=("Courier New", 14), text_color="gray").pack(side="left")

        card = ctk.CTkFrame(bg_frame, width=500, height=450, corner_radius=20, border_width=2, border_color="#F2A900")
        card.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(card, text="⚡", font=("Arial", 60), text_color="#F2A900").pack(pady=(30, 0))
        ctk.CTkLabel(card, text="MAGAZYN ZASOBÓW", font=("Impact", 36)).pack(pady=5)
        ctk.CTkLabel(card, text="Przyłóż kartę do czytnika", font=("Roboto", 14), text_color="gray").pack(pady=(0, 20))

        # self.rfid_entry = ctk.CTkEntry(card, width=300, placeholder_text="[CZEKANIE NA SYGNAŁ RFID...]", justify="center", font=("Courier New", 16))
        # self.rfid_entry.pack(pady=10)
        # self.rfid_entry.bind("<Return>", self.obsluga_skanu_rfid)
        
        # ctk.CTkButton(card, text="SYMULUJUJ SKANOWANIE", command=self.obsluga_skanu_rfid, fg_color="#333", hover_color="#444").pack(pady=5)

        # btns_frame = ctk.CTkFrame(card, fg_color="transparent")
        # btns_frame.pack(pady=20)
        # ctk.CTkLabel(btns_frame, text="Szybkie logowanie (DEBUG):", font=("Arial", 10), text_color="gray").pack(pady=5)
        #
        # ctk.CTkButton(btns_frame, text="USER_123", width=100, fg_color="#1F6AA5",
        #               command=lambda: self.symuluj_karty("USER_123")).pack(side="left", padx=5)
        # ctk.CTkButton(btns_frame, text="ADMIN_999", width=100, fg_color="#cf3030",
        #               command=lambda: self.symuluj_karty("ADMIN_999")).pack(side="right", padx=5)

        footer = ctk.CTkFrame(bg_frame, height=30, fg_color="#111")
        footer.pack(side="bottom", fill="x", pady=10, padx=10)
        self.lbl_status = ctk.CTkLabel(
            footer, 
            text="SERVER: CONNECTING... | DB: JSON | RFID: ...", 
            font=("Consolas", 10), 
            text_color="#555"
        )
        self.lbl_status.pack()

        # self.rfid_entry.focus_set()

    def aktualizuj_zegar(self):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        try:
            self.lbl_clock.configure(text=now)
            self.after(1000, self.aktualizuj_zegar)
        except: pass

    def sprawdz_rfid(self):
        if not self.winfo_exists():
            return
        try:
            response = requests.get(API_RFID, timeout=0.5)
            
            self.lbl_status.configure(
                text="SERVER: CONNECTED | DB: JSON | RFID: LISTENING",
                text_color="gray"  # Lub np. "#00E676" dla zielonego
            )
            if response.status_code == 200:
                data = response.json()
                card_id = data.get("card_id")

                if card_id:
                    print(f"DEBUG GUI: Próba logowania ID: '{card_id}' (typ: {type(card_id)})")
                    # Wywołujemy logowanie w głównym kontrolerze
                    self.app.zaloguj_uzytkownika(card_id)
                    return
        except Exception as e:
            self.lbl_status.configure(
                text="SERVER: DISCONNECTED | RFID: OFFLINE",
                text_color="#FF5252"
                )

        self.after(1000, self.sprawdz_rfid)
    # def symuluj_karty(self, kod_karty):
    #     """Wpisuje kod przycisku do pola i loguje"""
    #     self.rfid_entry.delete(0, "end")
    #     self.rfid_entry.insert(0, kod_karty)
    #     self.obsluga_skanu_rfid(None)
    #
    # def obsluga_skanu_rfid(self, event=None):
    #     """Pobiera tekst z pola (który wpisał czytnik lub my ręcznie) i loguje"""
    #     scanned_id = self.rfid_entry.get()
    #     if scanned_id:
    #         self.app.zaloguj_uzytkownika(scanned_id)
    #         self.rfid_entry.delete(0, "end")
