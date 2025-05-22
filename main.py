import uvicorn 

from src.services.log_pruner import LogPruner
from src.services.temporal_cache import TemporalCache
from src.services.sqlite_conn import SQliteConn
from src.application.api import API

if __name__ == "__main__":
    pruner: LogPruner = LogPruner(window_minutes=5)
    cache: TemporalCache = TemporalCache(pruner=pruner)
    sqlite: SQliteConn = SQliteConn(db_path = r"data/logs.db")
    api: API = API(cache=cache, db_service=sqlite)

    uvicorn.run(api.app)
