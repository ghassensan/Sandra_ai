from abc import ABC, abstractmethod
import typing as t
from pydantic import BaseModel
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from sandra_ai.models.cars_model import CarModel


T = t.TypeVar("T")


class Repository(BaseModel, t.Generic[T], ABC):
    model: t.Type[T]
    session: AsyncSession

    class Config:
        arbitrary_types_allowed = True

    @abstractmethod
    async def get_some(self, limit: int = 5) -> t.Sequence[T]:
        pass

    async def get(self, id: int) -> T | None:
        result = await self.session.execute(select(self.model).where(self.model.id == id))  # type: ignore

        return result.scalars().first()

    async def get_all(self) -> t.Sequence[T]:
        result = await self.session.execute(select(self.model))
        return result.scalars().all()

    async def add(self, entity: T) -> T:
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def delete(self, id: int) -> None:
        entity = await self.get(id)
        if entity:
            await self.session.delete(entity)
            await self.session.commit()

    async def delete_all(self) -> None:
        stmt = delete(self.model)
        await self.session.execute(stmt)
        await self.session.commit()

    async def update(self, id: int, updates: dict[t.Any, t.Any]) -> T | None:
        entity = await self.get(id)
        if entity:
            for key, value in updates.items():
                setattr(entity, key, value)
            await self.session.commit()
            await self.session.refresh(entity)
        return entity


class CarsRepository(Repository[CarModel]):
    async def get_some(self, limit: int = 5) -> t.Sequence[CarModel]:
        query = text("SELECT * FROM cars ORDER BY RANDOM() LIMIT :limit")
        result = await self.session.execute(query, {"limit": limit})
        return result.fetchall()  # type: ignore
