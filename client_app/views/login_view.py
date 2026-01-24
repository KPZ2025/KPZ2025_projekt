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

        card = ctk.CTkFrame(bg_frame, width=500, height=500, corner_radius=20, border_width=2, border_color="#F2A900")
        card.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(card, text="⚡", font=("Arial", 60), text_color="#F2A900").pack(pady=(30, 0))
        ctk.CTkLabel(card, text="MAGAZYN ZASOBÓW", font=("Impact", 36)).pack(pady=5)
        ctk.CTkLabel(card, text="Przyłóż kartę do czytnika lub wybierz opcję:", font=("Roboto", 14), text_color="gray").pack(pady=(0, 20))

        btns_frame = ctk.CTkFrame(card, fg_color="transparent")
        btns_frame.pack(pady=10)
        
        ctk.CTkButton(
            btns_frame, 
            text="MAGAZYNIER\n(4438933531)", 
            font=("Arial", 12, "bold"),
            fg_color="#F2A900", 
            text_color="black",
            hover_color="#D18F00",
            width=200,
            height=40,
            command=lambda: self.app.zaloguj_uzytkownika("4438933531")
        ).pack(pady=5)

        ctk.CTkButton(
            btns_frame, 
            text="UŻYTKOWNIK\n(44389335313)", 
            font=("Arial", 12),
            fg_color="#1F6AA5",
            hover_color="#144F7D", 
            width=200,
            height=40,
            command=lambda: self.app.zaloguj_uzytkownika("44389335313")
        ).pack(pady=5)

        ctk.CTkButton(
            btns_frame, 
            text="WERYFIKACJA DANYCH", 
            font=("Arial", 12),
            fg_color="#4A2574",
            hover_color="#144F7D", 
            width=200,
            height=40,
            command=lambda: self.app.uruchom_test_blockchain()
        ).pack(pady=5)

        footer = ctk.CTkFrame(bg_frame, height=30, fg_color="#111")
        footer.pack(side="bottom", fill="x", pady=10, padx=10)
        self.lbl_status = ctk.CTkLabel(
            footer, 
            text="SERVER: CONNECTING... | DB: JSON | RFID: ...", 
            font=("Consolas", 10), 
            text_color="#555"
        )
        self.lbl_status.pack()

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
                text_color="gray"
            )
            
            if response.status_code == 200:
                data = response.json()
                card_id = data.get("card_id")

                if card_id:
                    print(f"DEBUG GUI: Wykryto kartę RFID: '{card_id}'")
                    self.app.zaloguj_uzytkownika(card_id)
                    return
                    
        except Exception as e:
            self.lbl_status.configure(
                text="SERVER: DISCONNECTED | RFID: OFFLINE",
                text_color="#FF5252"
            )

        self.after(1000, self.sprawdz_rfid)