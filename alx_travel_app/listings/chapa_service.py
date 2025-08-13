import requests
import uuid
from django.conf import settings
from decouple import config
import logging

logger = logging.getLogger(__name__)

class ChapaService:
    def __init__(self):
        self.secret_key = config('CHAPA_SECRET_KEY')
        self.base_url = config('CHAPA_BASE_URL', default='https://api.chapa.co/v1')
        self.headers = {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json'
        }
    
    def initiate_payment(self, amount, currency, email, first_name, last_name, tx_ref, callback_url=None, return_url=None):
        """
        Initiate payment with Chapa
        """
        url = f"{self.base_url}/transaction/initialize"
        
        payload = {
            "amount": str(amount),
            "currency": currency,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "tx_ref": tx_ref,
            "callback_url": callback_url,
            "return_url": return_url,
            "customization": {
                "title": "ALX Travel App",
                "description": "Payment for booking"
            }
        }
        
        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Chapa payment initiation failed: {e}")
            return None
    
    def verify_payment(self, tx_ref):
        """
        Verify payment status with Chapa
        """
        url = f"{self.base_url}/transaction/verify/{tx_ref}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Chapa payment verification failed: {e}")
            return None