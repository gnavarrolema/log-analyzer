from sortedcontainers import SortedDict
from datetime import datetime

from src.model.log_entry import LogEntry
from src.services.log_pruner import LogPruner

class TemporalCache:
    def __init__(self, pruner: LogPruner):
        self.__pruner: LogPruner = pruner
        self.__cache: SortedDict = SortedDict()
        
    def add_log(self, log_entry: LogEntry) -> 'TemporalCache': 
        """Añade un nuevo log al cache temporal.

        Este método:
        1. Extrae el timestamp del log
        2. Registra el timestamp en el pruner para seguimiento
        3. Agrupa logs por timestamp en el cache

        Args:
            log_entry (LogEntry): Log a añadir al cache

        Returns:
            TemporalCache: Self para permitir encadenamiento de métodos

        Example:
            cache = TemporalCache(pruner)
            cache.add_log(log1).add_log(log2)  # Encadenamiento de métodos
        """
        timestamp: datetime = log_entry.timestamp
        self.__pruner.register_timestamp(timestamp)
        
        if timestamp not in self.__cache:
            self.__cache[timestamp] = list()
        self.__cache[timestamp].append(log_entry)
        return self
    
    def get_logs(self, start_time: datetime, end_time: datetime) -> list[LogEntry]:
        """Obtiene logs dentro de un rango temporal específico.

        Utiliza el método irange de SortedDict para obtener eficientemente
        los logs que caen dentro del intervalo [start_time, end_time].

        Args:
            start_time (datetime): Inicio del rango temporal (inclusive)
            end_time (datetime): Fin del rango temporal (inclusive)

        Returns:
            list[LogEntry]: Lista de logs dentro del rango especificado

        Example:
            logs = cache.get_logs(
                datetime(2023, 4, 23, 10, 0),
                datetime(2023, 4, 23, 10, 5)
            )
        """
        logs: list[LogEntry] = list()
        for timestamp in self.__cache.irange(start_time, end_time, inclusive=(True, True)):
            for log in self.__cache[timestamp]:
                logs.append(log)
        return logs
    
    def get_all_logs(self) -> list[LogEntry]:
        """Obtiene todos los logs almacenados en el cache.

        Returns:
            list[LogEntry]: Lista con todos los logs en orden temporal

        Note:
            Los logs se devuelven en el orden en que fueron almacenados
            debido a que SortedDict mantiene las claves ordenadas.
        """
        logs: list[LogEntry] = list()
        for timestamp in self.__cache:
            logs.extend(self.__cache[timestamp])
        return logs
        
    def prune_cache(self) -> list[LogEntry]:
        """Ejecuta la limpieza del cache eliminando logs antiguos.

        Delega la lógica de limpieza al LogPruner configurado,
        que determina qué logs deben ser eliminados basándose en
        la ventana temporal configurada.

        Returns:
            list[LogEntry]: Lista de logs que fueron eliminados del cache

        Note:
            Los logs eliminados se guardan en una base de datos
            para mantener un historial completo.
        """
        return self.__pruner.prune(self.__cache)