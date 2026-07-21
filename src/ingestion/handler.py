import json
from typing import Any, Dict
from aws_lambda_powertools import Logger, Tracer
from src.common.dynamodb import put_transaction

logger = Logger()
tracer = Tracer()

@tracer.capture_method
def process_record(record: Dict[str, Any]) -> None:
    sqs_body: Dict[str, Any] = json.loads(record.get("body", "{}"))
    sns_message_raw: str = sqs_body.get("Message", "{}")
    transaction_data: Dict[str, Any] = json.loads(sns_message_raw)
    
    logger.info("Procesando transaccion SQS", extra={"transaction": transaction_data})
    
    put_transaction({
        "user_id": str(transaction_data["user_id"]),
        "purchase_timestamp": str(transaction_data["purchase_timestamp"]),
        "purchase_id": str(transaction_data["purchase_id"]),
        "purchase_amount": int(transaction_data["purchase_amount"]),
        "purchase_items": [str(item) for item in transaction_data["purchase_items"]]
    })
