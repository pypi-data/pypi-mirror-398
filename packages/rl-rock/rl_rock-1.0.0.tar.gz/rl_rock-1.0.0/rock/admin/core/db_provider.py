from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from rock.admin.core.schema import DBModelBase

if TYPE_CHECKING:
    from rock.config import DatabaseConfig


class DatabaseProvider:
    def __init__(self, db_config: "DatabaseConfig"):
        self.db_config = db_config
        self.engine: AsyncEngine

    async def init(self):
        self.engine = create_async_engine(self.db_config.url, echo=True)

    async def create_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(DBModelBase.metadata.create_all)
