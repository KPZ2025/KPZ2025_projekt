import time
import requests
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

API_URL = "http://127.0.0.1:8000/api/rfid"

reader = SimpleMFRC522()

try:
    while True:
        card_id, _ = reader.read()
        print("RFID:", card_id)

        requests.post(API_URL, json={"card_id": str(card_id)})
        time.sleep(2)

except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()
