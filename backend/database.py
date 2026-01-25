import json
import os
import random
import uuid
import hashlib
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional, Any

DATA_DIR = 'data'
DB_FILE = os.path.join(DATA_DIR, 'db.json')
TRANS_FILE = os.path.join(DATA_DIR, 'transactions.json')
EXCHANGE_FILE = os.path.join(DATA_DIR, 'exchange.json')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
BLOCKCHAIN_FILE = os.path.join(DATA_DIR, 'blockchain.json')

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

class Block(BaseModel):
    index: int
    timestamp: str
    data: dict
    previous_hash: str
    hash: str

def load_json_file(filename) -> List[dict]:
    if not os.path.exists(filename): return []
    try:
        with open(filename, 'r', encoding='utf-8') as f: return json.load(f)
    except json.JSONDecodeError: return []

def save_json_file(filename, data: List[dict]):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def calculate_hash(index: int, timestamp: str, data: dict, previous_hash: str) -> str:
    data_str = json.dumps(data, sort_keys=True)
    block_string = f"{index}{timestamp}{data_str}{previous_hash}"
    return hashlib.sha256(block_string.encode()).hexdigest()

def init_blockchain():
    if not os.path.exists(BLOCKCHAIN_FILE):
        genesis_block = {
            "index": 0,
            "timestamp": datetime.now().isoformat(),
            "data": {"message": "Genesis Block - System Start"},
            "previous_hash": "0",
            "hash": ""
        }
        genesis_block["hash"] = calculate_hash(
            genesis_block["index"], 
            genesis_block["timestamp"], 
            genesis_block["data"], 
            genesis_block["previous_hash"]
        )
        save_json_file(BLOCKCHAIN_FILE, [genesis_block])

def add_blockchain_block(data_payload: dict):
    chain = load_json_file(BLOCKCHAIN_FILE)
    if not chain:
        init_blockchain()
        chain = load_json_file(BLOCKCHAIN_FILE)
    
    last_block = chain[-1]
    new_index = last_block['index'] + 1
    new_timestamp = datetime.now().isoformat()
    prev_hash = last_block['hash']
    
    new_hash = calculate_hash(new_index, new_timestamp, data_payload, prev_hash)
    
    new_block = {
        "index": new_index,
        "timestamp": new_timestamp,
        "data": data_payload,
        "previous_hash": prev_hash,
        "hash": new_hash
    }
    
    chain.append(new_block)
    save_json_file(BLOCKCHAIN_FILE, chain)
    print(f"[Blockchain] Dodano blok #{new_index}")


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

init_blockchain()