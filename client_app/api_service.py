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
