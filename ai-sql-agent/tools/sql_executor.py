from urllib.parse import quote_plus
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
import pandas as pd
from tools.paginator import wrap_with_pagination
from helpers.errors import ExecutionError

class MsSqlExecutor:
    def __init__(self, odbc_connect_str: str, timeout: int = 60):
        # Use ODBC connection string pass-through with SQLAlchemy. :contentReference[oaicite:9]{index=9}
        odbc_url = URL.create(
            "mssql+pyodbc",
            query={"odbc_connect": quote_plus(odbc_connect_str)},
        )
        self.engine = create_engine(
            odbc_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            fast_executemany=False,  # selects only
        )
        self.timeout = timeout

    def run_select(self, sql: str, page: int, page_size: int, hard_cap: int) -> pd.DataFrame:
        paged_sql = wrap_with_pagination(sql, page, page_size)
        try:
            with self.engine.connect() as conn:
                conn = conn.execution_options(stream_results=True)
                result = conn.execute(text(paged_sql))
                df = pd.DataFrame(result.fetchall(), columns=result.keys())
        except Exception as e:
            raise ExecutionError(str(e)) from e

        if df.shape[0] > hard_cap:
            df = df.head(hard_cap)
        return df
