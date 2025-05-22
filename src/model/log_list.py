from typing import List

from pydantic import BaseModel

from src.model.log_entry import LogEntry

class LogList(BaseModel):
    logs: List[LogEntry]