from typing import AsyncGenerator, List
from datetime import datetime
import enum 

from fastapi_users.db import (
    SQLAlchemyBaseOAuthAccountTable,
    SQLAlchemyBaseUserTable
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Boolean, ForeignKey, TIMESTAMP, Enum

from database import Base


class RoleType(str, enum.Enum):
    lead = 'lead'
    junior = 'junior'


# class OAuthAccount(SQLAlchemyBaseOAuthAccountTable[int], Base):
#     pass


class LocalAccount(SQLAlchemyBaseUserTable[int], Base):
    __tablename__ = 'localacc'

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True
    )
    email: Mapped[str] = mapped_column(
        String(length=125), unique=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(
        String(length=1024), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey('user.id', ondelete='CASCADE')
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean, default=False
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False
    )


class User(Base):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True
    )
    username: Mapped[str] = mapped_column(
        unique=True
    )
    first_name: Mapped[str] = mapped_column(
        nullable=False
    )
    last_name: Mapped[str] = mapped_column(
        nullable=False
    )
    registry_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime.now()
    )
    role: Mapped[RoleType] = mapped_column(
        Enum(RoleType), nullable=False
    )
