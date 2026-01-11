import json
import os
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from database import Product, load_json_file, DB_FILE, TransactionInput, TRANS_FILE, save_json_file, TransactionHistoryEntry

app = FastAPI(title="RPi Master Server")

@app.get("/api/products", response_model=List[Product])
def get_products():
    return load_json_file(DB_FILE)

@app.post("/api/transaction")
def process_transaction(trans: TransactionInput):
    products = load_json_file(DB_FILE)
    transactions = load_json_file(TRANS_FILE)
    
    product_found = False
    found_product_name = "Unknown"
    
    for item in products:
        if item['id'] == trans.product_id:
            item['qty'] += trans.qty_change
            
            if item['qty'] <= 0: item['status'] = "EMPTY"
            elif item['qty'] < 10: item['status'] = "LOW"
            else: item['status'] = "OK"
            
            product_found = True
            found_product_name = item['name']
            break
    
    if not product_found:
        raise HTTPException(status_code=404, detail="Produkt nieznaleziony")
    
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
    
    print(f"TRANSAKCJA: Produkt='{found_product_name}' Zmiana={trans.qty_change}")
    return {"message": "Success", "new_qty": item['qty']}

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

# uvicorn main:app --host 0.0.0.0 --port 8000 --reload