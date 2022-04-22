
from typing import Any, List
from sqlalchemy.ext.declarative import as_declarative, declared_attr

# base class
@as_declarative()
class Base:
    id: Any
    __name__: str

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

from sqlalchemy import Column, String, Table, BigInteger, Integer, func

# models
class MemorySQL(Base):
    """
    A model to be used by PostgreSQL_MemoryStoreProvider
    """

    __tablename__ = 'memories'
    created_at = Column(BigInteger, primary_key=True)
    author_id = Column(BigInteger, primary_key=True)
    author = Column(String, unique=False)
    text = Column(String, unique=False)
    encoding_model = Column(String, unique=False)
    encoding = Column(String)

# crud
from typing import Any, Generic, Optional, Type, TypeVar

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CrudBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, session: AsyncSession, id: Any) -> Optional[ModelType]:
        return (await session.execute(select(self.model).where(self.model.id == id))).scalars().first()

class CrudMemory(CrudBase[MemorySQL, MemorySQL, MemorySQL]):
    async def get_all(self, session: AsyncSession) -> List[MemorySQL]:
        return (await session.execute(select(self.model))).scalars().all()
    
    async def get_after_id(self, session: AsyncSession, created_at: int) -> List[MemorySQL]:
        return (await session.execute(select(self.model).where(self.model.created_at > created_at))).scalars().all()
    
    async def create(self, session: AsyncSession, created_at: int, author_id: int, author: str, text:str, encoding_model: str, encoding: str) -> MemorySQL:
        db_obj = MemorySQL(
            created_at=created_at,
            author_id=author_id,
            author=author,
            text=text,
            encoding_model=encoding_model,
            encoding=encoding
        )

        session.add(db_obj)
        await session.commit()

        return db_obj
    
    async def update(self, session: AsyncSession, created_at: str, author_id: int, author: str, text:str, encoding_model: str, encoding: str) -> MemorySQL:
        db_obj = (await session.execute(select(self.model).where(self.model.created_at == created_at))).scalars().first()
        
        if db_obj is None:
            return None

        db_obj.author_id = author_id
        db_obj.author = author
        db_obj.text = text
        db_obj.encoding_model = encoding_model
        db_obj.encoding = encoding

        await session.commit()

        return db_obj
    
    async def delete(self, session: AsyncSession, author_id: int) -> None:
        db_obj = (await session.execute(select(self.model).where(self.model.author_id == author_id))).scalars().first()
        
        if db_obj is None:
            return None
        
        await session.delete(db_obj)
        await session.commit()

        return None
    
    async def count(self, session: AsyncSession) -> int:
        return (await session.execute(select(func.count(self.model.created_at)))).scalars().first()

memory = CrudMemory(MemorySQL)