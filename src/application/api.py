from datetime import datetime

from fastapi import FastAPI, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from src.services.temporal_cache import TemporalCache
from src.services.sqlite_conn import SQliteConn
from src.model.log_entry import LogEntry
from src.model.log_list import LogList


class API:
    """API FastAPI para gestión de logs con cache temporal y almacenamiento persistente.
    
    Esta clase implementa una API RESTful que:
    1. Maneja la recepción y almacenamiento de logs
    2. Proporciona endpoints para consultar logs por rango temporal
    3. Gestiona la limpieza automática del cache
    4. Persiste logs antiguos en base de datos
    
    Attributes:
        __app (FastAPI): Instancia de FastAPI que maneja los endpoints
        __cache (TemporalCache): Cache temporal para almacenar logs recientes
        __db_service (SQliteConn): Servicio de base de datos para persistencia
    """
    def __init__(self, cache: TemporalCache, db_service: SQliteConn):
        self.__app = FastAPI(
            title = "Log API",
            description= "API for managing logs",
            version= "1.0.0",
        )
        self.__cache: TemporalCache = cache 
        self.__db_service: SQliteConn = db_service
        self.__set_up_routes()
    
    @property
    def app(self) -> FastAPI:
        return self.__app
    
    def __set_up_routes(self) -> 'API':
        """Configura las rutas de la API.

        Establece los endpoints disponibles:
        - POST /logs: Añadir nuevos logs
        - GET /logs: Obtener logs por rango temporal
        - GET /logs/all: Obtener todos los logs en cache

        Returns:
            API: Self para permitir encadenamiento
        """
        self.__app.post("/logs")(self.add_logs)
        self.__app.get("/logs")(self.get_logs)
        self.__app.get("/logs/all")(self.get_all_logs)
        return self
    
    def __prune_logs(self) -> list[LogEntry]:
        """Ejecuta la limpieza del cache temporal.

        Delega la limpieza al TemporalCache y retorna los logs eliminados
        para su posterior persistencia en base de datos.

        Returns:
            list[LogEntry]: Logs eliminados del cache
        """
        try:
            pruned_logs: list[LogEntry] = self.__cache.prune_cache()
            print(f"Pruned logs: {pruned_logs}")
            return pruned_logs
        except Exception as e:
            print(f"Error during pruning: {e}")
            
    def __save_pruned_logs(self, pruned_logs: list[LogEntry]) -> 'API':
        """Persiste los logs eliminados en la base de datos.

        Args:
            pruned_logs (list[LogEntry]): Logs a persistir

        Returns:
            API: Self para permitir encadenamiento
        """
        if not pruned_logs:
            return self
        
        self.__db_service.save_logs(pruned_logs)
        return self
            
    
    async def add_logs(self, log_list: LogEntry | LogList, background_task: BackgroundTasks) -> JSONResponse:
        """Añade uno o varios logs al sistema.

        Procesa la entrada (log individual o lista) y:
        1. Almacena los logs en el cache temporal
        2. Ejecuta limpieza (pruning) en background
        3. Persiste logs eliminados en base de datos

        Args:
            log_list (LogEntry | LogList): Log individual o lista de logs
            background_task (BackgroundTasks): Manejador de tareas en background

        Returns:
            JSONResponse: Confirmación con cantidad de logs procesados

        Example:
            POST /logs
            {
                "logs": [
                    {
                        "timestamp": "2023-04-23T10:00:00",
                        "tag": "INFO",
                        "message": "Test log"
                    }
                ]
            }
        """
        assert isinstance(log_list, (LogEntry, LogList)), "Invalid input type"
        
        if isinstance(log_list, LogList):
            logs: list[LogEntry] = log_list.logs
            for log_entry in logs:
                print(log_entry)
                self.__cache.add_log(log_entry)
            logs_count: int = len(logs)
        else:
             self.__cache.add_log(log_list)
             logs_count: int = 1
        
        background_task.add_task(self.__save_pruned_logs, self.__prune_logs())
        return JSONResponse(
            content={
                "message": f"Successfully added {logs_count} logs",
                "count": logs_count
            },
            status_code=201
        )
        
    async def get_logs(
        self, 
        start_time: datetime = Query(..., description="Start time in ISO format"), 
        end_time: datetime = Query(..., description="End time in ISO format")
    ) -> JSONResponse:
        """Obtiene logs dentro de un rango temporal específico.

        Este método:
        1. Busca primero en el cache temporal
        2. Si no encuentra logs en cache, busca en la base de datos
        3. Convierte los logs encontrados a formato JSON

        Args:
            start_time (datetime): Inicio del rango temporal en formato ISO (YYYY-MM-DDTHH:MM:SS)
            end_time (datetime): Fin del rango temporal en formato ISO (YYYY-MM-DDTHH:MM:SS)

        Returns:
            JSONResponse: Respuesta HTTP con:
                - content: {"logs": [lista de logs encontrados]}
                - media_type: "application/json"
                - status_code: 200

        Example:
            GET /logs?start_time=2023-04-23T10:00:00&end_time=2023-04-23T10:05:00
            
            Response:
            {
                "logs": [
                    {
                        "timestamp": "2023-04-23T10:00:00",
                        "tag": "INFO",
                        "message": "Test log"
                    }
                ]
            }
        """
        cache_logs: list[LogEntry] = self.__cache.get_logs(start_time, end_time)
        overall_logs: list[LogEntry] = self.__db_service.get_logs(start_time, end_time) \
            if not cache_logs else cache_logs  # buscamos en la base de datos si no estan en el cache
        jsonable_logs: list[dict] = [
            jsonable_encoder(log.model_dump() )
            for log in overall_logs
        ]
        
        return JSONResponse(content={"logs": jsonable_logs}, media_type="application/json", status_code=200)
    
    async def get_all_logs(self) -> JSONResponse:
        """Obtiene todos los logs almacenados en el cache temporal.

        Returns:
            JSONResponse: Lista completa de logs en cache

        Example:
            GET /logs/all
        """
        logs: list[LogEntry] = [
            jsonable_encoder(log.model_dump())
            for log in self.__cache.get_all_logs()
        ]
        return JSONResponse(content={"logs": logs}, media_type="application/json", status_code=200)
        
        