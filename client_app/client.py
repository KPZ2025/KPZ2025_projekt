import customtkinter as ctk
import datetime
from api_service import pobierz_produkty, wyslij_transakcje, pobierz_historie, sprawdz_uzytkownika, zaktualizuj_saldo

from views.login_view import LoginView
from views.resident_view import ResidentView
from views.warehouse_view import WarehouseView

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class SystemDystrybucjiApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("System Dystrybucji Zasobów")
        self.geometry("1024x600")

        self.produkty_db = []
        self.historia_zamowien = []
        
        self.odswiez_dane()
        
        self.uzycie_globalne = {}
        self.koszyk_uzytkownika = {}
        self.aktualny_uzytkownik = None
        self.user_card_id = None
        self.saldo_sesji = 0

        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)

        self.pokaz_ekran_logowania()

    def odswiez_dane(self):
        """Pobiera świeże produkty i historię z serwera"""
        self.produkty_db = pobierz_produkty()
        self.historia_zamowien = pobierz_historie()

    def wyczysc_ekran(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

    def pokaz_ekran_logowania(self):
        self.wyczysc_ekran()
        self.aktualny_uzytkownik = None
        self.user_card_id = None
        LoginView(self.main_container, self)

    def zaloguj_uzytkownika(self, user_id):
        user_data = sprawdz_uzytkownika(user_id)
        
        if not user_data:
            from tkinter import messagebox
            messagebox.showerror("Błąd", "Nieznana karta / Użytkownik nie istnieje.")
            return

        self.aktualny_uzytkownik = user_data['name']
        self.user_card_id = user_data['card_id']
        self.saldo_sesji = user_data['balance']
        role = user_data['role']

        self.odswiez_dane()
        
        if role == "admin":
            self.pokaz_ekran_magazynu()
        else:
            self.przelicz_uzycie_z_historii() 
            self.koszyk_uzytkownika = {}
            self.pokaz_ekran_mieszkanca()

    def przelicz_uzycie_z_historii(self):
        """Oblicza zużycie limitów TYLKO dla dzisiejszej daty"""
        self.uzycie_globalne[self.aktualny_uzytkownik] = {}
        moje_uzycie = {}
        
        dzisiaj_str = datetime.datetime.now().strftime("%Y-%m-%d")
        
        for wpis in self.historia_zamowien:
            if wpis.get('user_card_id') == self.user_card_id:
                
                czas_transakcji = wpis.get('timestamp', '')[:10]
                if czas_transakcji != dzisiaj_str:
                    continue

                p_name = wpis.get('product_name')
                found_prod = next((p for p in self.produkty_db if p['name'] == p_name), None)
                
                if found_prod:
                    pid = found_prod['id']
                    taken = abs(wpis['qty_change']) if wpis['qty_change'] < 0 else 0
                    
                    current_qty = moje_uzycie.get(pid, 0)
                    moje_uzycie[pid] = current_qty + taken

        self.uzycie_globalne[self.aktualny_uzytkownik] = moje_uzycie
        print(f"--- DEBUG: Zużycie na dzień {dzisiaj_str}: {moje_uzycie}")

    def pokaz_ekran_mieszkanca(self):
        self.wyczysc_ekran()
        ResidentView(self.main_container, self)

    def pokaz_ekran_magazynu(self):
        self.wyczysc_ekran()
        WarehouseView(self.main_container, self)

    def zmien_ilosc_w_koszyku(self, id_prod, delta):
        obecna = self.koszyk_uzytkownika.get(id_prod, 0)
        nowa = obecna + delta
        
        p = next((x for x in self.produkty_db if x['id'] == id_prod), None)
        if not p: return

        if nowa < 0: nowa = 0
        if nowa > p['qty']: return 
        
        temp_koszyk = self.koszyk_uzytkownika.copy()
        temp_koszyk[id_prod] = nowa
        if self.oblicz_koszt_calosci(temp_koszyk) > self.saldo_sesji:
            return

        self.koszyk_uzytkownika[id_prod] = nowa

    def oblicz_koszt_calosci(self, koszyk=None):
        if koszyk is None: koszyk = self.koszyk_uzytkownika
        total = 0
        for pid, ilosc in koszyk.items():
            if ilosc > 0:
                p = next((x for x in self.produkty_db if x['id'] == pid), None)
                if p:
                    juz_pobrano = self.uzycie_globalne[self.aktualny_uzytkownik].get(pid, 0)
                    
                    limit_free = p.get('limit_free', 0)
                    free_left = max(0, limit_free - juz_pobrano)
                    platne = max(0, ilosc - free_left)
                    
                    total += platne * p.get('extra_price', 0)
        return total

    def realizuj_zakup(self):
        koszt = self.oblicz_koszt_calosci()
        if koszt > self.saldo_sesji: return False

        sukces = True
        for pid, ilosc in self.koszyk_uzytkownika.items():
            if ilosc > 0:
                if not wyslij_transakcje(pid, -ilosc, self.user_card_id):
                    sukces = False
        
        if sukces:
            if koszt > 0:
                if zaktualizuj_saldo(self.user_card_id, koszt):
                    print(f"--- DEBUG: Zaktualizowano saldo na serwerze (-{koszt} T)")
                    self.saldo_sesji -= koszt
                else:
                    print("!!! BŁĄD: Nie udało się zaktualizować salda na serwerze!")

            for pid, ilosc in self.koszyk_uzytkownika.items():
                if ilosc > 0:
                    used = self.uzycie_globalne[self.aktualny_uzytkownik].get(pid, 0)
                    self.uzycie_globalne[self.aktualny_uzytkownik][pid] = used + ilosc

            self.koszyk_uzytkownika = {}
            self.odswiez_dane()
            return True
        return False

    def pokaz_custom_popup(self, tytul, podtytul):
        popup = ctk.CTkToplevel(self)
        try:
            x = self.winfo_x() + (self.winfo_width()//2) - 200
            y = self.winfo_y() + (self.winfo_height()//2) - 150
        except: x, y = 100, 100
        popup.geometry(f"400x300+{x}+{y}")
        popup.attributes("-topmost", True)
        
        ctk.CTkLabel(popup, text=tytul, font=("Arial", 20, "bold")).pack(pady=20)
        ctk.CTkLabel(popup, text=podtytul).pack(pady=10)
        ctk.CTkButton(popup, text="OK", command=popup.destroy, fg_color="#00E676", text_color="black").pack(pady=20)

if __name__ == "__main__":
    app = SystemDystrybucjiApp()
    app.mainloop()
