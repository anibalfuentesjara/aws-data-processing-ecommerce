from typing import Any, Dict
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, batch_processor

from src.ingestion.handler import process_record
from src.api.handler import app

logger = Logger()
tracer = Tracer()
processor = BatchProcessor(event_type=EventType.SQS)

@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    # Si viene de SQS
    if "Records" in event:
        return batch_processor(
            event=event, 
            context=context, 
            record_handler=process_record, 
            processor=processor
        )
    
    # Si viene de API Gateway
    return app.resolve(event, context)
