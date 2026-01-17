import json
import os
import random
import uuid
from filelock import FileLock
from pydantic import BaseModel
from typing import List, Optional

DATA_DIR = 'data'
DB_FILE = os.path.join(DATA_DIR, 'db.json')
TRANS_FILE = os.path.join(DATA_DIR, 'transactions.json')
EXCHANGE_FILE = os.path.join(DATA_DIR, 'exchange.json')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')

os.makedirs(DATA_DIR, exist_ok=True)

class Product(BaseModel):
    id: int
    name: str
    category: str
    qty: float
    unit: str
    status: str = "OK"
    extra_price: float
    limit_free: int
    limit_max: int

class TransactionInput(BaseModel):
    product_id: int
    qty_change: float
    user_card_id: str

class TransactionHistoryEntry(BaseModel):
    trans_id: str
    timestamp: str
    product_name: str
    qty_change: float
    unit: str
    user_card_id: str

class ExchangeOffer(BaseModel):
    id: Optional[str] = None
    user: str
    daje_nazwa: str
    daje_ilosc: int
    szuka_nazwa: str
    szuka_ilosc: int

class User(BaseModel):
    card_id: str
    name: str
    role: str
    balance: float

def generuj_nowe_oferty_npc(ilosc=3):
    imiona = ["Marek", "Anna", "Piotr", "Kasia", "Zygmunt", "Ewa", "Tomek", "Ola", "Jacek", "Monika"]
    zasoby = ["Chleb", "Woda", "Ryż", "Makaron", "Leki", "Tokeny"]
    nowe = []
    for _ in range(ilosc):
        imie = random.choice(imiona)
        suffix = random.randint(10, 99)
        co_daje = random.choice(zasoby)
        co_szuka = random.choice([z for z in zasoby if z != co_daje])
        oferta = {
            "id": f"npc_{uuid.uuid4()}", 
            "user": f"{imie}_{suffix}",
            "daje_nazwa": co_daje,
            "daje_ilosc": random.randint(1, 4),
            "szuka_nazwa": co_szuka,
            "szuka_ilosc": random.randint(1, 10)
        }
        nowe.append(oferta)
    return nowe

STARTOWI_UZYTKOWNICY = [
    {"card_id": "USER_123", "name": "Jan Kowalski", "role": "resident", "balance": 50.0},
    {"card_id": "ADMIN_999", "name": "Magazynier Szef", "role": "admin", "balance": 9999.0}
]

if os.path.exists(EXCHANGE_FILE):
    obecne = []
    try:
        with open(EXCHANGE_FILE, 'r', encoding='utf-8') as f: obecne = json.load(f)
    except: pass
    users_only = [o for o in obecne if not str(o.get('id', '')).startswith('npc_')]
    final_exch = users_only + generuj_nowe_oferty_npc(random.randint(3, 5))
    with open(EXCHANGE_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_exch, f, indent=4, ensure_ascii=False)
else:
    with open(EXCHANGE_FILE, 'w', encoding='utf-8') as f:
        json.dump(generuj_nowe_oferty_npc(4), f, indent=4, ensure_ascii=False)

if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(STARTOWI_UZYTKOWNICY, f, indent=4, ensure_ascii=False)

def load_json_file(filename) -> List[dict]:
    if not os.path.exists(filename): return []
    try:
        with open(filename, 'r', encoding='utf-8') as f: return json.load(f)
    except json.JSONDecodeError: return []

def save_json_file(filename, data: List[dict]):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
