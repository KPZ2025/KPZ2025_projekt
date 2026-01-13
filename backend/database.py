import json
import os
from filelock import FileLock
from pydantic import BaseModel
from typing import List, Optional

DATA_DIR = 'data'
DB_FILE = os.path.join(DATA_DIR, 'db.json')
TRANS_FILE = os.path.join(DATA_DIR, 'transactions.json')

os.makedirs(DATA_DIR, exist_ok=True)

class Product(BaseModel):
    id: int
    name: str
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


def load_json_file(filename) -> List[dict]:
    if not os.path.exists(filename):
        return []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_json_file(filename, data: List[dict]):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
