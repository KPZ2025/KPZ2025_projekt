import customtkinter as ctk
import datetime

class LoginView(ctk.CTkFrame):
    def __init__(self, parent, app_controller):
        super().__init__(parent, fg_color="transparent")
        self.app = app_controller
        self.pack(fill="both", expand=True)
        self.clock_loop = None
        self.create_widgets()

    def create_widgets(self):
        top_bar = ctk.CTkFrame(self, height=40, fg_color="transparent")
        top_bar.pack(fill="x", padx=20, pady=10)
        
        self.lbl_clock = ctk.CTkLabel(top_bar, text="00:00:00", font=("Courier New", 20, "bold"), text_color="#00E676")
        self.lbl_clock.pack(side="right")
        self.aktualizuj_zegar()
        
        ctk.CTkLabel(top_bar, text="SYSTEM v6.0 [CLIENT ONLINE]", font=("Courier New", 14), text_color="gray").pack(side="left")

        card = ctk.CTkFrame(self, width=500, height=400, corner_radius=20, border_width=2, border_color="#F2A900")
        card.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(card, text="⚡", font=("Arial", 60), text_color="#F2A900").pack(pady=(30, 0))
        ctk.CTkLabel(card, text="MAGAZYN ZASOBÓW", font=("Impact", 36)).pack(pady=5)
        ctk.CTkLabel(card, text="Terminal Autoryzacji", font=("Roboto", 14), text_color="gray").pack(pady=(0, 20))

        scan_area = ctk.CTkFrame(card, fg_color="#1a1a1a", corner_radius=10)
        scan_area.pack(pady=10, padx=40, fill="x")
        ctk.CTkLabel(scan_area, text=">>> OCZEKIWANIE NA TOKEN RFID <<<", font=("Courier New", 14, "bold"), text_color="#00E676").pack(pady=15)

        btns_frame = ctk.CTkFrame(card, fg_color="transparent")
        btns_frame.pack(pady=10)
        
        ctk.CTkButton(btns_frame, text="ID: MIESZKANIEC", 
                      command=lambda: self.app.zaloguj_uzytkownika("USER_123"), 
                      fg_color="#1F6AA5", width=180, height=50).pack(side="left", padx=10)
                      
        ctk.CTkButton(btns_frame, text="ID: MAGAZYNIER", 
                      command=lambda: self.app.zaloguj_uzytkownika("ADMIN_999"), 
                      fg_color="#cf3030", width=180, height=50).pack(side="right", padx=10)

        footer = ctk.CTkFrame(self, height=30, fg_color="#111")
        footer.pack(side="bottom", fill="x", pady=10, padx=10)
        ctk.CTkLabel(footer, text="STATUS: READY", font=("Consolas", 10), text_color="#555").pack()

    def aktualizuj_zegar(self):
        try:
            now = datetime.datetime.now().strftime("%H:%M:%S")
            self.lbl_clock.configure(text=now)
            self.clock_loop = self.after(1000, self.aktualizuj_zegar)
        except: pass
    
    def destroy(self):
        if self.clock_loop:
            self.after_cancel(self.clock_loop)
        super().destroy()
