from collections import deque
from datetime import datetime, timedelta

from sortedcontainers import SortedDict
from src.model.log_entry import LogEntry

class LogPruner:
    def __init__(self, window_minutes: int):
        self.__window_minutes: int = window_minutes
        self.__timestamps: deque[datetime] = deque()
    
    def register_timestamp(self, timestamp: datetime) -> 'LogPruner':
        """Registra un nuevo timestamp para el seguimiento temporal de logs.
    
        Este método mantiene un registro ordenado de timestamps que se utilizan
        para determinar qué logs deben ser eliminados del cache (pruning).
        Los timestamps se almacenan en una cola doblemente terminada (deque)
        para facilitar operaciones eficientes tanto al inicio como al final.
        
        Args:
            timestamp (datetime): Marca temporal del log a registrar
        
        Returns:
            LogPruner: Retorna self para permitir encadenamiento de métodos
        
        Example:
            pruner = LogPruner(window_minutes=5)
            pruner.register_timestamp(datetime.now())
        """
        self.__timestamps.append(timestamp)
        return self

    def prune(self, logs_cache: SortedDict) -> list[LogEntry]:
        """Elimina logs antiguos basándose en una ventana temporal deslizante.
    
        Este método implementa la lógica de limpieza del cache temporal:
        1. Encuentra el timestamp más reciente
        2. Calcula un umbral restando window_minutes al más reciente
        3. Elimina todos los logs anteriores al umbral
        
        Args:
            logs_cache (SortedDict): Diccionario ordenado que contiene los logs,
                                    donde las claves son timestamps y los valores
                                    son listas de LogEntry
        
        Returns:
            list[LogEntry]: Lista de logs que fueron eliminados del cache
        
        Example:
            cache = SortedDict()
            pruner = LogPruner(window_minutes=5)
            logs_eliminados = pruner.prune(cache)  # Elimina logs > 5 min
        
        Note:
            La ventana temporal se configura en el constructor de LogPruner
            mediante el parámetro window_minutes.
        """
        if not self.__timestamps:
            return list()
        
        most_recent: datetime = max(self.__timestamps)
        threshold = most_recent - timedelta(minutes=self.__window_minutes)
        pruned_logs = list()
        
        while self.__timestamps and self.__timestamps[0] < threshold:
            timestamp: datetime = self.__timestamps.popleft()
            if timestamp in logs_cache:
                pruned_logs.extend(logs_cache.pop(timestamp))
        
        return pruned_logs