from typing import Generic, Optional, Sequence, Type, TypeVar

from sqlalchemy import func, ColumnElement
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, SQLModel

T = TypeVar('T', bound=SQLModel)


class AsyncRepository(Generic[T]):
    def __init__(self, model: Type[T]):
        self.model = model

    async def count(self, session: AsyncSession, *conditions: ColumnElement) -> int:
        # pylint: disable=not-callable
        query = select(func.count()).select_from(self.model)

        if conditions:
            query = query.where(*conditions)

        result = await session.execute(query)
        return result.scalar_one()

    async def add(self, session: AsyncSession, entity: T) -> T:
        session.add(entity)

        await session.commit()
        await session.refresh(entity)

        return entity

    async def delete(self, session: AsyncSession, entity: T) -> None:
        await session.delete(entity)
        await session.commit()

    async def get(self, session: AsyncSession, *conditions: ColumnElement) -> Optional[T]:
        query = select(self.model)

        if conditions:
            query = query.where(*conditions)

        return (await session.execute(query)).scalars().first()

    async def list(self, session: AsyncSession, *conditions: ColumnElement[bool], offset: Optional[int] = None, order_by=None, limit: Optional[int] = None) -> Sequence[T]:
        query = select(self.model)

        if conditions:
            query = query.where(*conditions)

        if order_by is not None:
            query = query.order_by(order_by)

        if offset is not None:
            query = query.offset(offset)

        if limit is not None:
            query = query.limit(limit)

        return (await session.execute(query)).scalars().all()

    async def update(self, session: AsyncSession, entity: T, **kwargs) -> T:
        for key, value in kwargs.items():
            setattr(entity, key, value)

        session.add(entity)

        await session.commit()
        await session.refresh(entity)

        return entity
