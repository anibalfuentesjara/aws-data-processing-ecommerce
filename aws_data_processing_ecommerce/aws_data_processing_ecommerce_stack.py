from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
    aws_sqs as sqs,
    aws_lambda as _lambda,
    aws_lambda_event_sources as lambda_events,
    aws_logs as logs,
    aws_dynamodb as dynamodb,
    aws_apigateway as apigw
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
        ecommerce_lambda = _lambda.Function(
            self, "EcommerceLambdaFunction",
            function_name="ecommerce-processor-handler",
            runtime=_lambda.Runtime.PYTHON_3_11,
            code=_lambda.Code.from_asset("src"),  # Apunta a la raiz de src
            handler="main.handler",               # Apunta a src/main.py -> funcion handler
            timeout=Duration.seconds(15),
            log_retention=logs.RetentionDays.THREE_DAYS,
            environment={
                "POWERTOOLS_SERVICE_NAME": "ecommerce-service",
                "LOG_LEVEL": "INFO",
                "DYNAMODB_TABLE_NAME": table.table_name
            }
        )

        # 4. Configuración de Event Source Mapping e IAM
        # Permitir que SQS accione la Lambda de forma automática
        ecommerce_lambda.add_event_source(lambda_events.SqsEventSource(ingestion_queue))

        # Otorgar permisos de escritura explícitos a la Lambda sobre la tabla DynamoDB
        table.grant_read_write_data(ecommerce_lambda)

        # 4. API Gateway con protección por API Key (Fase 2)
        api = apigw.RestApi(
            self, "EcommerceApi",
            rest_api_name="Ecommerce Analytics API",
            description="API para consultar analytics e historial de usuarios",
            deploy_options=apigw.StageOptions(stage_name="prod")
        )

        # Integración de la Lambda con API Gateway (Proxy)
        lambda_integration = apigw.LambdaIntegration(ecommerce_lambda)

        # Recurso: /users/{user_id}/analytics
        users_resource = api.root.add_resource("users")
        user_id_resource = users_resource.add_resource("{user_id}")
        analytics_resource = user_id_resource.add_resource("analytics")

        # Método GET protegido por API Key
        analytics_resource.add_method(
            "GET",
            lambda_integration,
            api_key_required=True
        )

        # Crear API Key y Plan de Uso (Usage Plan)
        api_key = api.add_api_key(
            "EcommerceApiKey",
            api_key_name="ecommerce-client-key"
        )

        plan = api.add_usage_plan(
            "EcommerceUsagePlan",
            name="StandardUsagePlan",
            throttle=apigw.ThrottleSettings(
                rate_limit=10,
                burst_limit=20
            )
        )

        plan.add_api_stage(
            stage=api.deployment_stage
        )
        plan.add_api_key(api_key)
