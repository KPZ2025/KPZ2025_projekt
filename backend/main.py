import json
import os
import uuid
from datetime import datetime
from typing import List, Optional
# ZMIANA: Dodano BaseModel
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from database import Product, load_json_file, DB_FILE, TransactionInput, TRANS_FILE, save_json_file, TransactionHistoryEntry, ExchangeOffer, EXCHANGE_FILE, User, USERS_FILE

app = FastAPI(title="RPi Master Server")

class BalanceUpdate(BaseModel):
    amount: float

@app.get("/api/users/{card_id}", response_model=User)
def get_user_info(card_id: str):
    """Pobiera dane użytkownika (saldo, imię) na podstawie karty"""
    users = load_json_file(USERS_FILE)
    user = next((u for u in users if u['card_id'] == card_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="Użytkownik nieznany")
    return user

@app.post("/api/users/{card_id}/charge")
def update_user_balance(card_id: str, data: BalanceUpdate):
    users = load_json_file(USERS_FILE)
    
    user_idx = next((i for i, u in enumerate(users) if u['card_id'] == card_id), None)
    if user_idx is None:
        raise HTTPException(status_code=404, detail="Użytkownik nieznany")
    
    users[user_idx]['balance'] -= data.amount
    
    if users[user_idx]['balance'] < 0:
        users[user_idx]['balance'] = 0
        
    save_json_file(USERS_FILE, users)
    
    return {"message": "Saldo zaktualizowane", "new_balance": users[user_idx]['balance']}

@app.post("/api/transaction")
def process_transaction(trans: TransactionInput):
    products = load_json_file(DB_FILE)
    transactions = load_json_file(TRANS_FILE)
    users = load_json_file(USERS_FILE)
    
    product_found = False
    item_obj = None
    for item in products:
        if item['id'] == trans.product_id:
            item_obj = item
            product_found = True
            break
    
    if not product_found:
        raise HTTPException(status_code=404, detail="Produkt nieznaleziony")

    user_idx = next((i for i, u in enumerate(users) if u['card_id'] == trans.user_card_id), None)
    if user_idx is None:
        raise HTTPException(status_code=404, detail="Nieznany użytkownik")

    item_obj['qty'] += trans.qty_change
    if item_obj['qty'] <= 0: item_obj['status'] = "EMPTY"
    elif item_obj['qty'] < 10: item_obj['status'] = "LOW"
    else: item_obj['status'] = "OK"

    save_json_file(DB_FILE, products)
    
    new_history_record = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "product_id": trans.product_id,
        "qty_change": trans.qty_change,
        "user_card_id": trans.user_card_id
    }
    transactions.append(new_history_record)
    save_json_file(TRANS_FILE, transactions)
    
    print(f"TRANSAKCJA: User={trans.user_card_id} Produkt='{item_obj['name']}' Zmiana={trans.qty_change}")
    return {"message": "Success", "new_qty": item_obj['qty']}


@app.get("/api/products", response_model=List[Product])
def get_products():
    return load_json_file(DB_FILE)

@app.get("/api/history", response_model=List[TransactionHistoryEntry])
def get_transaction_history():
    products = load_json_file(DB_FILE)
    transactions = load_json_file(TRANS_FILE)
    products_map = {p['id']: p for p in products} 
    history_response = []
    for t in reversed(transactions):
        product_details = products_map.get(t['product_id'])
        p_name = product_details['name'] if product_details else f"USUNIĘTY (ID: {t['product_id']})"
        p_unit = product_details['unit'] if product_details else "?"
        entry = TransactionHistoryEntry(
            trans_id=t['id'],
            timestamp=t['timestamp'],
            product_name=p_name,
            qty_change=t['qty_change'],
            unit=p_unit,
            user_card_id=t['user_card_id']
        )
        history_response.append(entry)
    return history_response

@app.get("/api/exchange", response_model=List[ExchangeOffer])
def get_offers():
    return load_json_file(EXCHANGE_FILE)

@app.post("/api/exchange")
def add_offer(offer: ExchangeOffer):
    offers = load_json_file(EXCHANGE_FILE)
    offer.id = str(uuid.uuid4())
    offers.append(offer.dict())
    save_json_file(EXCHANGE_FILE, offers)
    return {"message": "Oferta dodana", "id": offer.id}

@app.delete("/api/exchange/{offer_id}")
def delete_offer(offer_id: str):
    offers = load_json_file(EXCHANGE_FILE)
    new_offers = [o for o in offers if o['id'] != offer_id]
    if len(offers) == len(new_offers):
        raise HTTPException(status_code=404, detail="Oferta nie znaleziona")
    save_json_file(EXCHANGE_FILE, new_offers)
    return {"message": "Oferta usunięta"}

@app.post("/api/products")
def add_new_product(prod: Product):
    products = load_json_file(DB_FILE)
    
    if any(p['name'].lower() == prod.name.lower() for p in products):
        raise HTTPException(status_code=400, detail="Produkt o tej nazwie już istnieje")
    
    new_id = 1
    if products:
        new_id = max(p['id'] for p in products) + 1
    
    prod.id = new_id
    
    products.append(prod.dict())
    save_json_file(DB_FILE, products)
    
    return {"message": "Produkt dodany", "id": new_id}
