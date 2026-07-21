# Pasos desarrollo

## Estructura de Pasos

Pasos Iniciales (Sin CI/CD):
0. Creación del repositorio en github.
1. Configuración del entorno local e inicialización del proyecto AWS CDK con Python.
2. Diseño de la tabla de DynamoDB (Single Table Design si aplica, definiendo PK/SK para las consultas de compras y analíticas del último mes).
3. Creación de la infraestructura de Ingestión en CDK (SNS, SQS y la Lambda de procesamiento) y configuración de permisos IAM.
4. Código de la Lambda de Ingestión usando AWS Lambda Powertools para procesar los mensajes de SQS que vienen de SNS.
5. Creación de la infraestructura del API Gateway (con configuración de API Key) y la Lambda de lectura en CDK.
6. Código de la Lambda del Endpoint usando Powertools (Event Handler), queries/scans optimizados a DynamoDB y lógica de procesamiento de datos con DuckDB.
7. Pruebas de integración locales/remotas para validar que los datos se guardan y se consultan correctamente.

Pasos de CI/CD (Solo tras finalizar y validar los anteriores):

8. Configuración del pipeline de CI/CD con CDK/GitHub para automatizar los despliegues a producción tras hacer push.

### 0. Creación del repositorio en github.

Se crea un nuevo repositorio, se clona en local y se agrega el .gitignore

### 1. Configuración del entorno local e inicialización del proyecto AWS CDK con Python.

* Necesitamos uv, node (se instala la v24.18), npm (se instala la 11.16) y aws cli configurado.
* Instalar cdk (npm install -g aws-cdk)
* Crear ambiente virtual con uv (`uv venv --python 3.11`) y activarlo (`.venv\Scripts\Activate.ps1`)
* Inicializar la app de AWS CDK (`cdk init app --language python`) . Si este paso arroja error porque el repositorio no está vacío entonces hay que mover los archivos actuales a un directorio temporal, ejecutar el comando, y mover los archivos de vuelta.
* Instalar las dependencias con uv (`uv pip install -r requirements.txt`)
* Verificar la inicialización del stack de CDK con `cdk ls` . Debiese responder `AwsDataProcessingEcommerceStack`

### 2. Diseño de la tabla de DynamoDB

Se diseñará una única tabla para almacenar la información de las compras, los campos de la tabla son:

* user_id (varchar) : identificador único del usuario (uuid). Será el partition key.
* purchase_timestamp (timestamp) : iso timestamp de la transacción. Será el sort key.
* purchase_id (varchar) : identificador único de la transacción. Índice global secundario.
* purchase_amount (int): monto total de la transacción
* purchase_items (array<varchar>): lista de ids de los productos de la transacción 

### 3. Creación de la infraestructura de Ingestión en CDK (SNS, SQS y la Lambda de procesamiento) y configuración de permisos IAM.

Se crea la infraestructura (como código) para la ingestión de eventos utilizando CDK. Para esto se modifica el stack en `aws_data_processing_ecommerce\aws_data_processing_ecommerce_stack.py`


### 4. Código de la Lambda de Ingestión usando AWS Lambda Powertools para procesar los mensajes de SQS que vienen de SNS.

Se implementa el código de ingestión de la lambda en `src\ingestion\handler.py`. 

Algunas notas:

* Se utiliza el Logger de lambda powertools para manejar los logs
* Se utiliza el Tracer de lambda powertools para proveer observabilidad: Mide tiempos y rutas, Visualización de mapas de servicios, Captura de Metadatos y Errores
* Se utiliza BatchProcessor para procesar los mensajes de SQS. Si se envía un batch de 10 mensajes y falla uno solo este se reenvía a la DQL.

### 5. Creación de la infraestructura del API Gateway (con configuración de API Key) y la Lambda de lectura en CDK.

Se modifica el archivo `aws_data_processing_ecommerce\aws_data_processing_ecommerce_stack.py` y se agrega el api gateway.

### 6. Código de la Lambda del Endpoint usando Powertools (Event Handler), queries/scans optimizados a DynamoDB y lógica de procesamiento de datos con DuckDB.

Implementamos el código de la dynamo en `src\common\dynamodb.py` y el código de duckdb en `src\common\duckdb.py`

Separamos el código de ingestión.

Implementamos el código de la api en `src\api\handler.py`

Implementamos el handler de la lambda en `src\main.py`

### 7. Pruebas de integración locales/remotas para validar que los datos se guardan y se consultan correctamente.

Si es la primera vez utilizando cdk, debemos realizar el bootstrapping: `cdk bootstrap aws://843335492713/us-west-2`

Luego `cdk synth`

Y finalmente `cdk deploy`

Prueba ingestión eventos:

```
aws sns publish `
  --topic-arn "<SNS_TOPIC_ARN>" `
  --message '{\"user_id\": \"USR_123\", \"purchase_id\": \"TX_001\", \"purchase_timestamp\": \"2026-07-20T10:00:00Z\", \"purchase_amount\": 15000, \"purchase_items\": [\"item1\", \"item2\"]}'
```