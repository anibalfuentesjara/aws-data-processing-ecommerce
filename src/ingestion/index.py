import os
import json
import boto3
from typing import Any, Dict
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.data_classes import SQSEvent, event_source
from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, batch_processor

# Inicialización de utilidades de Powertools y cliente DynamoDB
logger = Logger()
tracer = Tracer()
processor = BatchProcessor(event_type=EventType.SQS)

# Obtener variables de entorno inyectadas por CDK
TABLE_NAME: str = os.environ.get("DYNAMODB_TABLE_NAME", "transactions")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

@tracer.capture_method
def record_handler(record: Dict[str, Any]) -> None:
    """
    Procesa un registro individual de SQS. 
    Nota que el mensaje original de SNS viene serializado en el campo 'body'.
    """
    # 1. Parsear el cuerpo del registro de SQS
    sqs_body: Dict[str, Any] = json.loads(record.get("body", "{}"))
    
    # 2. El mensaje real enviado a SNS está en el campo 'Message'
    sns_message_raw: str = sqs_body.get("Message", "{}")
    transaction_data: Dict[str, Any] = json.loads(sns_message_raw)
    
    logger.info("Procesando transaccion del e-commerce", extra={"transaction": transaction_data})
    
    # 3. Extraer y validar campos requeridos (Tipado estricto)
    user_id: str = str(transaction_data["user_id"])
    purchase_timestamp: str = str(transaction_data["purchase_timestamp"])
    purchase_id: str = str(transaction_data["purchase_id"])
    purchase_amount: int = int(transaction_data["purchase_amount"])
    purchase_items: list[str] = [str(item) for item in transaction_data["purchase_items"]]
    
    # 4. Inserción directa en DynamoDB usando la PK y SK acordadas
    table.put_item(
        Item={
            "user_id": user_id,                      # Partition Key
            "purchase_timestamp": purchase_timestamp, # Sort Key
            "purchase_id": purchase_id,
            "purchase_amount": purchase_amount,
            "purchase_items": purchase_items
        }
    )
    logger.info(f"Transaccion {purchase_id} guardada con exito para el usuario {user_id}")

@event_source(data_class=SQSEvent)
@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
@batch_processor(record_handler=record_handler, processor=processor)
def handler(event: SQSEvent, context: Any) -> Dict[str, Any]:
    """
    Manejador principal de la Lambda (Híbrido).
    Por ahora procesa lotes de SQS de forma segura. Si un registro falla, 
    Powertools se encarga de reportar la falla parcial a SQS automáticamente.
    """
    return processor.response()
