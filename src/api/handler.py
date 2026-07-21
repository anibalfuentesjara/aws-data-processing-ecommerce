import json
from typing import Any, Dict, List
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import ApiGatewayResolver, Response, content_types

from src.common.dynamodb import get_user_transactions_last_month
from src.common.duckdb import DuckDBManager

logger = Logger()
tracer = Tracer()
app = ApiGatewayResolver()

@app.get("/users/<user_id>/analytics")
@tracer.capture_method
def get_user_analytics(user_id: str) -> Response:
    logger.info(f"Consultando analytics para el usuario: {user_id}")
    
    # 1. Obtener registros crudos de DynamoDB
    items: List[Dict[str, Any]] = get_user_transactions_last_month(user_id)
    
    if not items:
        return Response(
            status_code=200,
            content_type=content_types.APPLICATION_JSON,
            body=json.dumps({
                "user_id": user_id,
                "is_active": False,
                "total_transactions_last_month": 0,
                "total_amount_spent": 0
            })
        )

    # 2. Inicializar DuckDB y cargar datos dinámicamente sin esquemas hardcodeados
    db = DuckDBManager()
    db.load_db_from_dynamo_records(records=items, table_name="transactions")
    
    # 3. Ejecutar query agnóstica de agregación
    sql_query = """
        SELECT 
            COUNT(purchase_id) as total_txs,
            COALESCE(SUM(purchase_amount), 0) as total_spent
        FROM transactions
    """
    
    results = db.query_db(sql_query)
    
    total_txs = results[0][0] if results else 0
    total_spent = results[0][1] if results else 0

    return Response(
        status_code=200,
        content_type=content_types.APPLICATION_JSON,
        body=json.dumps({
            "user_id": user_id,
            "is_active": total_txs > 0,
            "total_transactions_last_month": total_txs,
            "total_amount_spent": int(total_spent)
        })
    )
