import os
import boto3
from typing import Any, Dict, List
from datetime import datetime, timedelta, timezone

TABLE_NAME: str = os.environ.get("DYNAMODB_TABLE_NAME", "transactions")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

def put_transaction(item: Dict[str, Any]) -> None:
    """Guarda una transaccion en DynamoDB."""
    table.put_item(Item=item)

def get_user_transactions_last_month(user_id: str) -> List[Dict[str, Any]]:
    """Consulta optimizada usando PK (user_id) y SK (purchase_timestamp >= hace 30 dias)."""
    one_month_ago: str = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    
    response = table.query(
        KeyConditionExpression="user_id = :uid AND purchase_timestamp >= :from_date",
        ExpressionAttributeValues={
            ":uid": user_id,
            ":from_date": one_month_ago
        }
    )
    return response.get("Items", [])
