from typing import ClassVar
from datetime import datetime
from functools import lru_cache

from os.path import abspath, exists
from sqlite3 import connect, Cursor

from src.model.log_entry import LogEntry

class SQliteConn:
    NON_EXISTENT_PATH: ClassVar[str] = "The path to the database does not exist."
    CREATE_TABLE_QUERY: ClassVar[str] = """
    CREATE TABLE IF NOT EXISTS {} (
        timestamp TEXT NOT NULL,
        tag TEXT NOT NULL,
        message TEXT NOT NULL
    )
    """
    GET_LOGS_QUERY: ClassVar[str] = """
    SELECT 
        timestamp, tag, message 
    FROM 
        {}
    WHERE 
        timestamp BETWEEN ? AND ?;
    """
    
    def __init__(self, db_path: str, logs_table: str = "logs"):
        self.__db_path: str = abspath(db_path)
        assert exists(self.__db_path), self.NON_EXISTENT_PATH
        
        self.__logs_table: str = logs_table
        self.__init_db_connection()
    
    def __init_db_connection(self) -> None:
        """Inicializa la conexión a la base de datos SQLite y crea la tabla si no existe.
    
        Este método es llamado durante la inicialización del SQliteConn y se encarga de:
        1. Establecer la conexión inicial con la base de datos
        2. Crear la tabla de logs si no existe
        3. Asegurar que la base de datos está lista para almacenar logs
        
        Note:
            La estructura de la tabla se define en CREATE_TABLE_QUERY y contiene:
            - timestamp: TEXT - Marca temporal del log
            - tag: TEXT - Nivel o categoría del log
            - message: TEXT - Contenido del mensaje
        """
        with connect(self.__db_path) as conn:
            conn.execute(self.CREATE_TABLE_QUERY.format(self.__logs_table))
            conn.commit()
        return
    
    def save_logs(self, logs: list[LogEntry] | LogEntry) -> None:
        """Guarda uno o varios logs en la base de datos SQLite.
    
        Este método maneja tanto logs individuales como listas de logs:
        1. Convierte el input en una lista si es un log individual
        2. Inserta los logs en la base de datos usando una única transacción
        3. Muestra información sobre el rango temporal de los logs guardados
        
        Args:
            logs (list[LogEntry] | LogEntry): Log individual o lista de logs a guardar
        
        Raises:
            ConnectionError: Si ocurre un error durante la conexión o inserción en la base de datos
        
        Example:
            sqlite_conn = SQliteConn("logs.db")
            log = LogEntry(timestamp=datetime.now(), tag="INFO", message="Test")
            sqlite_conn.save_logs(log)  # Guarda un log individual
            sqlite_conn.save_logs([log1, log2])  # Guarda múltiples logs
        
        Note:
            Los timestamps se convierten a formato ISO antes de guardarse
            para garantizar consistencia en el almacenamiento.
        """
        if not logs:
            return
        
        with connect(self.__db_path) as conn:
            try:
                logs = list(logs) if not isinstance(logs, list) else logs
                
                conn.executemany(
                    f"INSERT INTO {self.__logs_table} (timestamp, tag, message) VALUES (?, ?, ?)",
                    [(log.timestamp.isoformat(), log.tag, log.message) for log in logs]
                )
                conn.commit()
                print(
                    f"Saved {len(logs)} logs to database "
                    f"(from {min(logs).timestamp.isoformat()} to {max(logs).timestamp.isoformat()})"
                )
            except Exception as e:
                conn.rollback()
                raise ConnectionError(f"Error saving logs to database: {e}") from e
            
    @lru_cache(maxsize=50)  # agregamos cache a las consultas a la base de datos. 
    def get_logs(self, start_time: datetime, end_time: datetime) -> list[LogEntry]:
        """Recupera logs dentro de un rango de tiempo específico.

        Args:
            start_time (str): Timestamp inicial en formato ISO (YYYY-MM-DDTHH:MM:SS)
            end_time (str): Timestamp final en formato ISO (YYYY-MM-DDTHH:MM:SS)

        Returns:
            list[LogEntry]: Lista de logs encontrados en el rango especificado

        Raises:
            ConnectionError: Si ocurre un error durante la consulta a la base de datos
        """
        
        print(f"Searching in DB from {start_time} to {end_time}")
        
        with connect(self.__db_path) as conn:
            try:
                cursor: Cursor = conn.execute(self.GET_LOGS_QUERY.format(self.__logs_table), (start_time.isoformat(), end_time.isoformat()))
                logs: list[LogEntry] = [LogEntry.from_db_row(row) for row in cursor] 
                return logs
            except Exception as e:
                raise ConnectionError(f"Error retrieving logs from database: {e}") from e
    