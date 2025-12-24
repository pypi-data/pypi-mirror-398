import psycopg
from fastapi_lifespan_manager import LifespanManager
from psycopg.abc import Query
from psycopg.rows import DictRow, dict_row
from psycopg_pool.pool_async import AsyncConnectionPool as DBConnAsyncPool
from pydantic import Field

from apppy.env import Env, EnvSettings
from apppy.logger import WithLogger


class PostgresClientSettings(EnvSettings):
    # POSTGRES_DB_CONN
    conn: str = Field()
    # POSTGRES_DB_HOST
    host: str = Field()
    # POSTGRES_DB_PASSWORD
    password: str = Field(exclude=True)
    # POSTGRES_DB_POOL_MIN_SIZE
    pool_min_size: int = Field(default=4)
    # POSTGRES_DB_POOL_MAX_SIZE
    pool_max_size: int | None = Field(default=None)
    # POSTGRES_DB_POOL_TIMEOUT
    pool_timeout: float = Field(default=30)

    def __init__(self, env: Env) -> None:
        super().__init__(env=env, domain_prefix="POSTGRES_DB")


class PostgresClient(WithLogger):
    def __init__(self, settings: PostgresClientSettings, lifespan: LifespanManager) -> None:
        self._settings = settings

        self._conninfo: str = f"host={settings.host} password={settings.password} {settings.conn}"
        self._db_pool_async: DBConnAsyncPool | None = None
        lifespan.add(self.__open_db_pool_async)

    async def __open_db_pool_async(self):
        self._logger.info("Opening Postgres psycopg_pool_async")
        if not self._db_pool_async or self._db_pool_async.closed:
            self._db_pool_async = DBConnAsyncPool(
                conninfo=self._conninfo,
                open=False,
                min_size=self._settings.pool_min_size,
                max_size=self._settings.pool_max_size,
                timeout=self._settings.pool_timeout,
            )
            self._logger.info(
                "Opened Postgres psycopg_pool_async",
                extra={
                    "min_size": self._settings.pool_min_size,
                    "max_size": self._settings.pool_max_size,
                },
            )

        await self._db_pool_async.open(wait=True)
        yield {"db_pool_async": self._db_pool_async}

        self._logger.info("Closing Postgres psycopg_pool_async")
        try:
            await self._db_pool_async.close()
        except Exception:
            self._logger.exception("Error while closing Postgres psycopg_pool_async")

    @property
    def db_pool_async(self) -> DBConnAsyncPool:
        if self._db_pool_async is None:
            raise Exception("Postgres db_pool_async is uninitialized")

        return self._db_pool_async

    async def db_query_async(self, query: Query, params: dict | None = None) -> list[DictRow]:
        async with (
            self.db_pool_async.connection() as db_conn,
            psycopg.AsyncClientCursor(db_conn, row_factory=dict_row) as db_cursor_async,
        ):
            await db_cursor_async.execute(query=query, params=params)
            result_set = await db_cursor_async.fetchall()

            return result_set
