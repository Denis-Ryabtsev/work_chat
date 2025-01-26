from typing import Annotated, Optional
from datetime import datetime
import enum 

from fastapi_users.db import SQLAlchemyBaseUserTable
from sqlalchemy.orm import (
    Mapped, 
    mapped_column, 
    relationship
)
from sqlalchemy import (
    Integer, 
    String, 
    Boolean, 
    ForeignKey,
    TIMESTAMP, 
    Enum
)
#

from database import Base


int_pk = Annotated[int, mapped_column(primary_key=True, autoincrement=True)]


class RoleType(str, enum.Enum):
    lead = 'lead'
    junior = 'junior'


# class OAuthAccount(Base):
#     __tablename__ = 'oauth_account'

#     id: Mapped[int_pk]
#     oauth_name: Mapped[str] = mapped_column(
#         String(length=100), index=True, nullable=False
#     )
#     access_token: Mapped[str] = mapped_column(
#         String(length=1024), nullable=False
#     )
#     expires_at: Mapped[Optional[int]] = mapped_column(
#         Integer, nullable=True
#     )
#     refresh_token: Mapped[Optional[str]] = mapped_column(
#         String(length=1024), nullable=True
#     )
#     account_id: Mapped[str] = mapped_column(
#         String(length=320), index=True, nullable=False
#     )
#     account_email: Mapped[str] = mapped_column(
#         String(length=320), nullable=False
#     )
#     user_id: Mapped[int] = mapped_column(
#         ForeignKey(f'user.id', ondelete=f'CASCADE')
#     )

#     user = relationship(f'User', back_populates=f'oauth')


class GithubAccount(Base):
    __tablename__ = f'github_account'

    id: Mapped[int_pk]
    login: Mapped[str] = mapped_column(
        unique=True, nullable=False
    )
    account_id: Mapped[str] = mapped_column(
        unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(
        default=None
    )
    token: Mapped[str] = mapped_column(
        nullable=False
    )
    avatar_url: Mapped[str] = mapped_column(
        default=None
    )


class LocalAccount(SQLAlchemyBaseUserTable[int], Base):
    __tablename__ = f'local_account'

    id: Mapped[int_pk]
    email: Mapped[str] = mapped_column(
        String(length=125), unique=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(
        String(length=1024), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey('user.id', ondelete='CASCADE')
    )
    oauth_id: Mapped[int] = mapped_column(
        default=None, unique=True
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

    # user_acc = relationship(f'User', back_populates=f'local')


class User(Base):
    __tablename__ = f'user'

    id: Mapped[int_pk]
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

    # oauth = relationship(f'OAuthAccount', back_populates=f'user')
    # local = relationship(f'LocalAccount', back_populates=f'user_acc')


