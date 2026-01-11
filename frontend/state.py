from nicegui import ui
import httpx
import json
import os
import asyncio
from datetime import datetime

SERVER_URL = 'http://127.0.0.1:8000'
LOCAL_CACHE_FILE = 'client_cache.json'

class DataManager:
    def __init__(self):
        self.products = []
        self.history = []
        self.last_update = "Nigdy"
        self.load_from_local()

    def load_from_local(self):
        if os.path.exists(LOCAL_CACHE_FILE):
            try:
                with open(LOCAL_CACHE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.products = data.get('products', [])
                    self.history = data.get('history', [])
                    self.last_update = data.get('last_update', 'Nieznana')
            except Exception as e:
                print(f"Błąd odczytu cache: {e}")

    def save_to_local(self):
        data = {
            'products': self.products,
            'history': self.history,
            'last_update': datetime.now().strftime("%H:%M:%S")
        }
        with open(LOCAL_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        self.last_update = data['last_update']

    async def fetch_from_server(self):
        async with httpx.AsyncClient(timeout=3.0) as client:
            try:
                resp_prod = await client.get(f"{SERVER_URL}/api/products")
                if resp_prod.status_code != 200:
                    return False, f"Błąd serwera: {resp_prod.status_code}"
                resp_hist = await client.get(f"{SERVER_URL}/api/history") 
                
                self.products = resp_prod.json()
                if resp_hist.status_code == 200:
                    self.history = resp_hist.json()
                
                self.save_to_local()
                return True, "Zaktualizowano pomyślnie"

            except httpx.ConnectError:
                return False, "Nie można połączyć z serwerem"
            except Exception as e:
                return False, f"Błąd: {str(e)}"

db=DataManager()

session_info = {'user': None}

def logout():
    session_info['user'] = None
    ui.navigate.to('/')