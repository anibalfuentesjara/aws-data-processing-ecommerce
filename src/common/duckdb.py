import duckdb
from typing import Any, Dict, List, Optional
from aws_lambda_powertools import Logger

logger = Logger()

class DuckDBManager:
    """
    Clase para gestionar una base de datos DuckDB en memoria dentro del ciclo de vida de la Lambda.
    Permite cargar registros dinamicos de DynamoDB y ejecutar consultas SQL arbitrarias.
    """
    
    def __init__(self) -> None:
        # Inicializa una conexion aislada en memoria
        self._con: duckdb.DuckDBPyConnection = duckdb.connect(database=":memory:")
        logger.debug("Conexion a DuckDB en memoria inicializada.")

    def load_db_from_dynamo_records(
        self, 
        records: List[Dict[str, Any]], 
        table_name: str = "transactions"
    ) -> None:
        """
        Recibe una lista de diccionarios (registros de DynamoDB) y los registra directamente 
        como una tabla virtual en DuckDB infiriendo tipos y esquemas de forma automatica.
        
        :param records: Lista de registros extraidos de DynamoDB.
        :param table_name: Nombre de la tabla virtual que se registrara en DuckDB.
        """
        if not records:
            logger.warning(f"No hay registros para cargar en la tabla '{table_name}'.")
            return

        # DuckDB puede consultar directamente listas de diccionarios en Python usando Arrow/Relation API
        # Creamos una relacion dinamica basada en la estructura de Python y la registramos como vista/tabla
        rel = self._con.from_df(self._convert_to_arrow_friendly_dict(records))
        rel.create(table_name)
        
        logger.info(f"Cargados {len(records)} registros exitosamente en la tabla virtual '{table_name}'.")

    def query_db(self, query: str, params: Optional[List[Any]] = None) -> List[tuple]:
        """
        Ejecuta una consulta SQL sobre los datos cargados en memoria y retorna los resultados.
        
        :param query: Sentencia SQL a ejecutar.
        :param params: Parametros opcionales para parametrizar la consulta de forma segura.
        :return: Lista de tuplas con el resultado de la consulta.
        """
        logger.debug(f"Ejecutando query en DuckDB: {query}")
        
        if params:
            return self._con.execute(query, params).fetchall()
        return self._con.execute(query).fetchall()

    def query_db_to_dict(self, query: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
        """
        Ejecuta una consulta SQL y retorna los resultados estructurados como una lista de diccionarios 
        (clave: nombre de columna, valor: resultado).
        """
        cursor = self._con.execute(query, params) if params else self._con.execute(query)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        
        return [dict(zip(columns, row)) for row in rows]

    def _convert_to_arrow_friendly_dict(self, records: List[Dict[str, Any]]) -> Dict[str, List[Any]]:
        """
        Transforma una lista de diccionarios [ {col1: val1}, {col1: val2} ] 
        a un diccionario de listas { col1: [val1, val2] } que DuckDB / Arrow procesan en tiempo récord.
        """
        if not records:
            return {}
        
        # Obtener la union de todas las llaves presentes en los registros
        keys = set().union(*(d.keys() for d in records))
        
        columns_dict: Dict[str, List[Any]] = {key: [] for key in keys}
        for record in records:
            for key in keys:
                # Si una llave no existe en un registro especifico, se inserta None (NULL)
                columns_dict[key].append(record.get(key, None))
                
        return columns_dict