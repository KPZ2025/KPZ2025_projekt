import customtkinter as ctk
import datetime
from api_service import pobierz_produkty, wyslij_transakcje, pobierz_historie, sprawdz_uzytkownika, zaktualizuj_saldo, sprawdz_blockchain
import threading
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

    def odswiez_dane(self, products_only=False):
        """Pobiera świeże produkty i historię z serwera"""
        self.produkty_db = pobierz_produkty()
        if not products_only:
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
        self.configure(cursor="watch")
        
        threading.Thread(target=self._login_in_background, args=(user_id,), daemon=True).start()

    def _login_in_background(self, user_id):
        try:
            user_data = sprawdz_uzytkownika(user_id)
            self.after(0, lambda: self._finish_login(user_data))
        except Exception as e:
            print(f"Błąd sieci: {e}")
            self.after(0, lambda: self._finish_login(None))

    def _finish_login(self, user_data):
        self.configure(cursor="arrow")
        if not user_data:
            from tkinter import messagebox
            messagebox.showerror("Błąd", "Nieznana karta / Użytkownik nie istnieje.")
            self.pokaz_ekran_logowania()
            return

        self.aktualny_uzytkownik = user_data['name']
        self.user_card_id = user_data['card_id']
        self.saldo_sesji = user_data['balance']
        role = user_data['role']

        self.odswiez_dane(products_only=False)
        
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

    def uruchom_test_blockchain(self):
        self.configure(cursor="watch")
        threading.Thread(target=self._watek_testu_blockchain, daemon=True).start()

    def _watek_testu_blockchain(self):
        wynik = sprawdz_blockchain()
        self.after(0, lambda: self._pokaz_wynik_blockchain(wynik))

    def _pokaz_wynik_blockchain(self, result):
        self.configure(cursor="arrow")
        
        window = ctk.CTkToplevel(self)
        window.geometry("600x500")
        window.title("Raport Integralności Systemu")
        window.attributes("-topmost", True)
        window.wait_visibility()
        window.grab_set()

        ctk.CTkLabel(window, text="RAPORT BLOCKCHAIN", font=("Impact", 24)).pack(pady=15)

        is_valid = result.get("chain_valid", False)
        length = result.get("blockchain_length", 0)
        
        status_color = "#00E676" if is_valid else "#FF1744"
        status_text = "SYSTEM SPÓJNY" if is_valid else "WYKRYTO BŁĘDY!"
        icon = "🛡️" if is_valid else "⚠️"

        frame_status = ctk.CTkFrame(window, fg_color="transparent", border_width=2, border_color=status_color)
        frame_status.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(frame_status, text=f"{icon} {status_text}", font=("Arial", 20, "bold"), text_color=status_color).pack(pady=10)
        ctk.CTkLabel(frame_status, text=f"Długość łańcucha: {length} bloków", text_color="gray").pack(pady=(0, 10))

        errors = result.get("errors", [])
        if errors:
            ctk.CTkLabel(window, text="LISTA BŁĘDÓW:", font=("Roboto", 12, "bold"), text_color="#FF1744").pack(pady=(10, 5), anchor="w", padx=20)
            
            scroll_err = ctk.CTkScrollableFrame(window, fg_color="#2b0000")
            scroll_err.pack(fill="both", expand=True, padx=20, pady=10)
            
            for err in errors:
                row = ctk.CTkFrame(scroll_err, fg_color="transparent")
                row.pack(fill="x", pady=2)
                ctk.CTkLabel(row, text="❌", text_color="#FF1744").pack(side="left", padx=(0,5))
                lbl = ctk.CTkLabel(row, text=err, anchor="w", justify="left", wraplength=500)
                lbl.pack(side="left", fill="x", expand=True)
        else:
            ctk.CTkLabel(window, text="Wszystkie bloki są poprawnie powiązane kryptograficznie.\nStany magazynowe i salda zgadzają się z historią.", 
                         text_color="#aaa", font=("Roboto", 12)).pack(pady=20)

        ctk.CTkButton(window, text="ZAMKNIJ", fg_color="#333", command=window.destroy).pack(pady=20)

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
            self.odswiez_dane(products_only=True)
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
