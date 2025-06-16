from uuid import UUID, uuid1
from datetime import datetime
from sqlalchemy.sql import func
from sqlalchemy.types import Uuid
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Mapped, relationship, mapped_column
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid1)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    sub: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    api_key: Mapped[str] = mapped_column(String(length=64), unique=True, nullable=False)
    admin: Mapped[bool] = mapped_column(Boolean, default=False)
    images = relationship('Image', back_populates='user')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Image(Base):
    __tablename__ = 'images'

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid1)
    uid: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    original_name: Mapped[str] = mapped_column(String, nullable=False)
    extension: Mapped[str] = mapped_column(String, nullable=False)
    content_type: Mapped[str] = mapped_column(String, nullable=False)
    deletion_key: Mapped[str] = mapped_column(String(length=64), unique=True, nullable=False)
    size: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey('users.id'), nullable=False)
    user = relationship('User', back_populates='images')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
