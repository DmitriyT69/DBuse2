from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from app.backend.db import Base


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[Optional[str]]
    firstname: Mapped[Optional[str]]
    lastname: Mapped[Optional[str]]
    age: Mapped[Optional[int]]
    slug: Mapped[Optional[str]] = mapped_column(unique=True, index=True)
    tasks: Mapped[List['Task']] = relationship(back_populates='user',
                                               cascade='all, delete',
                                               passive_deletes=True)