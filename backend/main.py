import json
import os
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from database import (
    Product, load_json_file, DB_FILE, TransactionInput, TRANS_FILE, 
    save_json_file, TransactionHistoryEntry, ExchangeOffer, EXCHANGE_FILE, 
    User, USERS_FILE, BLOCKCHAIN_FILE, add_blockchain_block, calculate_hash
)

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
    
    old_balance = users[user_idx]['balance']
    users[user_idx]['balance'] -= data.amount
    
    if users[user_idx]['balance'] < 0:
        users[user_idx]['balance'] = 0
        
    save_json_file(USERS_FILE, users)
    
    add_blockchain_block({
        "type": "BALANCE_CHARGE",
        "user_card_id": card_id,
        "amount_deducted": data.amount,
        "old_balance": old_balance,
        "new_balance": users[user_idx]['balance']
    })
    
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
    
    add_blockchain_block({
        "type": "PRODUCT_TRANSACTION",
        "user_card_id": trans.user_card_id,
        "product_id": trans.product_id,
        "product_name": item_obj['name'],
        "qty_change": trans.qty_change,
        "new_qty": item_obj['qty']
    })
    
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
    
    add_blockchain_block({
        "type": "OFFER_ADDED",
        "offer_id": offer.id,
        "user": offer.user,
        "details": f"{offer.daje_ilosc} {offer.daje_nazwa} -> {offer.szuka_ilosc} {offer.szuka_nazwa}"
    })
    
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
    
    add_blockchain_block({
        "type": "NEW_PRODUCT",
        "product_id": new_id,
        "name": prod.name,
        "initial_qty": prod.qty
    })
    
    return {"message": "Produkt dodany", "id": new_id}


@app.get("/api/integrity")
def check_system_integrity():
    chain = load_json_file(BLOCKCHAIN_FILE)
    users = load_json_file(USERS_FILE)
    products = load_json_file(DB_FILE)
    
    status = {
        "chain_valid": True,
        "errors": [],
        "blockchain_length": len(chain)
    }
    
    for i in range(1, len(chain)):
        current = chain[i]
        previous = chain[i-1]
        
        if current['previous_hash'] != previous['hash']:
            status['chain_valid'] = False
            status['errors'].append(f"Przerwany łańcuch w bloku #{current['index']}. Poprzedni hash nie pasuje.")
        
        recalculated_hash = calculate_hash(
            current['index'], 
            current['timestamp'], 
            current['data'], 
            current['previous_hash']
        )
        if recalculated_hash != current['hash']:
            status['chain_valid'] = False
            status['errors'].append(f"Manipulacja danymi w bloku #{current['index']}! Hash nie pasuje do zawartości.")

    if not status['chain_valid']:
        return status
    
    user_ids = []
    for block in reversed(chain):
        if block['data'].get('type') == 'BALANCE_CHARGE':
            user_id = block['data']['user_card_id']
            recorded_new_balance = block['data']['new_balance']
            
            current_user = next((u for u in users if u['card_id'] == user_id), None)
            if current_user and user_id not in user_ids:
                user_ids.append(user_id)
                if abs(current_user['balance'] - recorded_new_balance) > 0.01:
                    status['errors'].append(f"Ostrzeżenie: Saldo usera {user_id} ({current_user['balance']}) różni się od ostatniego zapisu w blockchain ({recorded_new_balance}).")
                    break
        
    for product in products:
        for block in reversed(chain):
            if(block['data'].get('product_id')==product['id']):
                if(block['data'].get('new_qty')!=product['qty']):
                    print(block['data'].get('new_qty'))
                    status['errors'].append("Wrong quantity for product "+product['name'])
                break
            
    if status['errors']:
        status['chain_valid'] = False
        
    return status


class RFIDData(BaseModel):
    card_id: str

LAST_RFID = None

@app.post("/api/rfid")
def rfid_scan(data: RFIDData):
    global LAST_RFID
    LAST_RFID = data.card_id
    print(f"Server: Odebrano ID z czytnika: {LAST_RFID}")
    return {"ok": True}

@app.get("/api/rfid")
def get_rfid():
    global LAST_RFID
    temp = LAST_RFID
    LAST_RFID = None
    
    return {"card_id": temp}