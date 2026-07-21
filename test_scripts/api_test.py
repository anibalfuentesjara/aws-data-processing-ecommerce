import os
import requests
from dotenv import load_dotenv

# Cargar variables del archivo .env
load_dotenv()

API_URL = os.getenv("API_URL")
API_KEY = os.getenv("API_KEY")

def test_analytics_api(user_id: str = "USR_123") -> None:
    if not API_URL or not API_KEY:
        raise ValueError("Error: API_URL y/o API_KEY no están definidos en el archivo .env")

    # Eliminar barras diagonales al final si existen
    base_url = API_URL.rstrip("/")
    endpoint = f"{base_url}/users/{user_id}/analytics"
    
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    print(f"🔍 Consultando endpoint analítico para usuario '{user_id}': {endpoint}")
    
    response = requests.get(endpoint, headers=headers)
    
    print(f"Status Code: {response.status_code}")
    print("Respuesta:")
    print(response.json())

if __name__ == "__main__":
    test_analytics_api("USR_1")
