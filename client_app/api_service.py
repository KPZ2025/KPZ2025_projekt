import requests

SERVER_URL = "http://127.0.0.1:8000"

def pobierz_produkty():
    try:
        response = requests.get(f"{SERVER_URL}/api/products")
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Błąd API: {e}")
    return []

def wyslij_transakcje(product_id, zmiana_ilosci, user_card_id):
    payload = {
        "product_id": product_id,
        "qty_change": zmiana_ilosci,
        "user_card_id": user_card_id
    }
    try:
        response = requests.post(f"{SERVER_URL}/api/transaction", json=payload)
        return response.status_code == 200
    except:
        return False

def pobierz_historie():
    try:
        response = requests.get(f"{SERVER_URL}/api/history")
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Błąd API (historia): {e}")
    return []

def pobierz_oferty():
    """Pobiera listę ofert z serwera"""
    try:
        response = requests.get(f"{SERVER_URL}/api/exchange")
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Błąd API (pobierz oferty): {e}")
    return []

def dodaj_oferte(user, daje_n, daje_i, szuka_n, szuka_i):
    """Wysyła nową ofertę na serwer"""
    payload = {
        "user": user,
        "daje_nazwa": daje_n,
        "daje_ilosc": int(daje_i),
        "szuka_nazwa": szuka_n,
        "szuka_ilosc": int(szuka_i)
    }
    try:
        response = requests.post(f"{SERVER_URL}/api/exchange", json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"Błąd API (dodaj ofertę): {e}")
        return False

def usun_oferte(offer_id):
    """Usuwa ofertę (akceptacja)"""
    try:
        response = requests.delete(f"{SERVER_URL}/api/exchange/{offer_id}")
        return response.status_code == 200
    except Exception as e:
        print(f"Błąd API (usuń ofertę): {e}")
        return False

def dodaj_nowy_produkt_db(nazwa, kategoria, ilosc, jednostka, cena_extra, limit_free, limit_max):
    """Wysyła żądanie utworzenia zupełnie nowego produktu"""
    payload = {
        "id": 0,
        "name": nazwa,
        "category": kategoria,
        "qty": float(ilosc),
        "unit": jednostka,
        "status": "OK",
        "extra_price": float(cena_extra),
        "limit_free": int(limit_free),
        "limit_max": int(limit_max)
    }
    try:
        response = requests.post(f"{SERVER_URL}/api/products", json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"Błąd API (dodaj produkt): {e}")
        return False

def sprawdz_uzytkownika(card_id):
    """Pyta serwer o dane użytkownika na podstawie karty"""
    try:
        response = requests.get(f"{SERVER_URL}/api/users/{card_id}")
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Błąd logowania: {e}")
    return None

def zaktualizuj_saldo(card_id, kwota_do_odjecia):
    """Wysyła informację o zmianie salda do serwera (trwała zmiana w users.json)"""
    payload = {"amount": float(kwota_do_odjecia)}
    try:
        response = requests.post(f"{SERVER_URL}/api/users/{card_id}/charge", json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"Błąd API (saldo): {e}")
        return False

def sprawdz_blockchain():
    try:
        response = requests.get(f"{SERVER_URL}/api/integrity")
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        return {
            "chain_valid": False, 
            "errors": [f"Błąd połączenia z serwerem: {str(e)}"], 
            "blockchain_length": 0
        }
    return {"chain_valid": False, "errors": ["Nieznany błąd"], "blockchain_length": 0}