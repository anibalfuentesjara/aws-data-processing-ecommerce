from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
    aws_sqs as sqs,
    aws_lambda as _lambda,
    aws_lambda_event_sources as lambda_events,
    aws_dynamodb as dynamodb,
)
from constructs import Construct

class AwsDataProcessingEcommerceStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. Tabla de DynamoDB: transactions
        # Optimizada con user_id (PK) y purchase_timestamp (SK)
        table = dynamodb.Table(
            self, "TransactionsTable",
            table_name="transactions",
            partition_key=dynamodb.Attribute(
                name="user_id", 
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="purchase_timestamp", 
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            # DESTROY solo para desarrollo/aprendizaje. Cambiar a RETAIN en producción.
            removal_policy=RemovalPolicy.DESTROY, 
        )

        # 2. Componentes de mensajería (Fase 1)
        # Tópico de SNS que recibirá los eventos del e-commerce
        ecommerce_topic = sns.Topic(
            self, "EcommerceTopic",
            topic_name="ecommerce-transactions-topic"
        )

        # Cola SQS que amortiguará los mensajes para la Lambda
        ingestion_queue = sqs.Queue(
            self, "IngestionQueue",
            queue_name="ecommerce-ingestion-queue",
            visibility_timeout=Duration.seconds(30) # Debe ser >= al timeout de la Lambda
        )

        # Suscribir la cola SQS al tópico SNS
        ecommerce_topic.add_subscription(subs.SqsSubscription(ingestion_queue))

        # 3. Lambda de Ingestión
        # Capa de código que procesará los mensajes de la cola
        ingestion_lambda = _lambda.Function(
            self, "IngestionLambdaFunction",
            function_name="ecommerce-ingestion-handler",
            runtime=_lambda.Runtime.PYTHON_3_11,
            code=_lambda.Code.from_asset("src/ingestion"), # Carpeta que crearemos en el siguiente paso
            handler="index.handler",
            timeout=Duration.seconds(15),
            environment={
                "POWERTOOLS_SERVICE_NAME": "ecommerce-ingestion",
                "LOG_LEVEL": "INFO",
                "DYNAMODB_TABLE_NAME": table.table_name
            }
        )

        # 4. Configuración de Event Source Mapping e IAM
        # Permitir que SQS accione la Lambda de forma automática
        ingestion_lambda.add_event_source(lambda_events.SqsEventSource(ingestion_queue))

        # Otorgar permisos de escritura explícitos a la Lambda sobre la tabla DynamoDB
        table.grant_write_data(ingestion_lambda)