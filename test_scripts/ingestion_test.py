import os
import json
import boto3
from dotenv import load_dotenv

# Cargar variables del archivo .env en la raiz
load_dotenv()

SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN")
AWS_REGION = os.getenv("AWS_REGION", "us-west-2")

def test_sns_ingestion() -> None:
    if not SNS_TOPIC_ARN:
        raise ValueError("Error: SNS_TOPIC_ARN no esta definido en el archivo .env")

    sns_client = boto3.client("sns", region_name=AWS_REGION)
    
    # Payload simulado de una compra
    payload = {
        "user_id": "USR_1",
        "purchase_id": "TX_001",
        "purchase_timestamp": "2026-07-20T10:00:00Z",
        "purchase_amount": 15000,
        "purchase_items": ["item1", "item2"]
    }
    
    print(f"Enviando mensaje de prueba a SNS: {SNS_TOPIC_ARN}")
    
    response = sns_client.publish(
        TopicArn=SNS_TOPIC_ARN,
        Message=json.dumps(payload)
    )
    
    print(f"Mensaje publicado con éxito. MessageId: {response.get('MessageId')}")

if __name__ == "__main__":
    test_sns_ingestion()
