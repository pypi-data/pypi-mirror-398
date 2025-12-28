from typing import Generic, List, Sequence, Type, TypeVar

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from ..data.repositories import AsyncRepository
from ..data import async_session

T = TypeVar('T', bound=SQLModel)


class BaseRouter(Generic[T]):
    def __init__(self, model: Type[T], repo: AsyncRepository[T], prefix: str, tags: List[str]):
        self.model  = model
        self.repo   = repo
        self.router = APIRouter(prefix=prefix, tags=tags)

        self._setup_routes()

    @staticmethod
    async def _get_session():
        async with async_session() as session:
            yield session

    async def _before_add(self, entity: T, session: AsyncSession) -> None:
        pass

    # pylint: disable=unused-argument
    async def _after_add(self, entity: T, session: AsyncSession) -> None:
        await session.commit()

    async def _before_delete(self, entity: T, session: AsyncSession) -> None:
        pass

    # pylint: disable=unused-argument
    async def _after_delete(self, entity: T, session: AsyncSession) -> None:
        await session.commit()

    # pylint: disable=unused-argument
    async def _before_update(self, entity: T, data: dict, session: AsyncSession) -> None:
        pass

    # pylint: disable=unused-argument
    async def _after_update(self, entity: T, session: AsyncSession) -> None:
        await session.commit()

    def _setup_routes(self) -> None:
        @self.router.post('/', response_model=self.model, status_code=status.HTTP_201_CREATED)
        async def add(data: dict = Body(...), session: AsyncSession = Depends(BaseRouter._get_session)) -> T:
            entity = self.model(**data)

            await self._before_add(entity, session)
            result = await self.repo.add(session, entity)
            await self._after_add(result, session)

            return result

        @self.router.delete('/{id}', status_code=status.HTTP_204_NO_CONTENT)
        async def delete(id: str, session: AsyncSession = Depends(BaseRouter._get_session)) -> None:
            entity = await self.repo.get(session, self.model.id == id)
            if not entity:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

            await self._before_delete(entity, session)
            await self.repo.delete(session, entity)
            await self._after_delete(entity, session)

        @self.router.get('/{id}', response_model=self.model)
        async def get(id: str, session: AsyncSession = Depends(BaseRouter._get_session)) -> T:
            entity = await self.repo.get(session, self.model.id == id)
            if not entity:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

            return entity

        @self.router.get('/', response_model=List[self.model])
        async def list(response: Response, session: AsyncSession = Depends(BaseRouter._get_session), offset: int = Query(None, ge=0), limit: int = Query(None, ge=1, le=100)) -> Sequence[T]:
            response.headers['X-Total-Count'] = str(await self.repo.count(session))

            return await self.repo.list(session, offset=offset, limit=limit)

        @self.router.put('/{id}', response_model=self.model)
        async def update(id: str, data: dict = Body(...), session: AsyncSession = Depends(BaseRouter._get_session)) -> T:
            entity = await self.repo.get(session, self.model.id == id)
            if not entity:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

            await self._before_update(entity, data, session)

            for key, value in data.items():
                setattr(entity, key, value)

            result = await self.repo.update(session, entity)
            await self._after_update(result, session)

            return result
