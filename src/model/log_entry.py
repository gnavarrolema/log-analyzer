from datetime import datetime

from pydantic import BaseModel


#@dataclass
class LogEntry(BaseModel):
    timestamp: datetime
    tag: str  # e.g., "INFO", "ERROR", "DEBUG"
    message: str
    
    def __lt__(self, other: 'LogEntry'):
        """Compara dos objetos LogEntry basándose en sus timestamps.
    
        Este método mágico permite realizar operaciones de comparación entre logs,
        lo cual es necesario para:
        1. Ordenar logs cronológicamente
        2. Encontrar el log más antiguo/reciente usando min()/max()
        3. Mantener el orden temporal en colecciones de logs
        
        Ejemplo:
            log1 = LogEntry(timestamp=datetime.now(), tag="INFO", message="Primer log")
            log2 = LogEntry(timestamp=datetime.now(), tag="ERROR", message="Segundo log")
            log_mas_antiguo = min(log1, log2)  # Retorna el log con timestamp más antiguo
        
        Args:
            other (LogEntry): Otro objeto LogEntry con el cual comparar
        
        Returns:
            bool: True si el timestamp de este log es más antiguo que el otro
        
        Raises:
            TypeError: Si se intenta comparar con un objeto que no es LogEntry
        
        Note:
            Este método es fundamental para el funcionamiento del cache temporal
            y el proceso de limpieza (pruning) de logs antiguos.
        """
        assert isinstance(other, LogEntry), NotImplemented
        return self.timestamp < other.timestamp
    
    @staticmethod
    def from_db_row(row: tuple) -> 'LogEntry':
        """Crea una instancia de LogEntry desde una tupla de la base de datos.
    
        Este método estático convierte una fila de la base de datos en un objeto LogEntry,
        esperando los campos en el siguiente orden:
        - row[0]: timestamp en formato ISO (YYYY-MM-DDTHH:MM:SS)
        - row[1]: tag del log (e.g., "INFO", "ERROR")
        - row[2]: mensaje del log
        
        Args:
            row (tuple): Tupla con los datos del log desde la base de datos
            
        Returns:
            LogEntry: Nueva instancia de LogEntry con los datos de la fila
            
        Example:
            db_row = ("2023-04-23T10:00:00", "INFO", "Test message")
            log = LogEntry.from_db_row(db_row)
            
        Note:
            El timestamp debe estar en formato ISO para poder ser parseado correctamente
            por datetime.fromisoformat()
        """
        return LogEntry(
            timestamp=datetime.fromisoformat(row[0]),
            tag=row[1],
            message=row[2]
        )
    
    class Config:
        frozen = True