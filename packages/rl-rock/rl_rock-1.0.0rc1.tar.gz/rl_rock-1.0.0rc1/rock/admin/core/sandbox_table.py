from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from rock.admin.core.schema import SandboxRecord


class SandboxTable:
    def __init__(self, engine: AsyncEngine):
        self._engine = engine

    async def create(self, sandbox_record: SandboxRecord):
        async with AsyncSession(self._engine) as session:
            session.add(sandbox_record)
            await session.commit()

    async def list(
        self, namespace: str | None = None, user: str | None = None, experiment_id: str | None = None
    ) -> Sequence[SandboxRecord]:
        async with AsyncSession(self._engine) as session:
            stmt = select(SandboxRecord)
            if None is not namespace:
                stmt = stmt.where(SandboxRecord.namespace == namespace)
            if None is not user:
                stmt = stmt.where(SandboxRecord.user == user)
            if None is not experiment_id:
                stmt = stmt.where(SandboxRecord.experiment_id == experiment_id)
            result = await session.execute(stmt)
            return result.scalars().all()

    async def get(self, id: str) -> SandboxRecord:
        async with AsyncSession(self._engine) as session:
            return await session.get(SandboxRecord, id)
