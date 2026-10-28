"""
Configuração do banco de dados relacional e sessão SQLAlchemy.
Suporta PostgreSQL para desenvolvimento/produção e SQLite para testes automatizados.
"""

from typing import Generator
import uuid
from sqlalchemy import JSON, create_engine
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.types import CHAR, TypeDecorator

from app.core.config import settings


class GUID(TypeDecorator):
    """
    Tipo de coluna independente de plataforma para UUID.
    Utiliza o tipo nativo UUID no PostgreSQL e CHAR(36) no SQLite.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return str(value) if dialect.name != "postgresql" else value
        return str(uuid.UUID(str(value))) if dialect.name != "postgresql" else uuid.UUID(str(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if not isinstance(value, uuid.UUID):
            return uuid.UUID(str(value))
        return value


class JSONType(TypeDecorator):
    """
    Tipo de coluna para dados JSON independente de plataforma.
    Utiliza JSONB no PostgreSQL e JSON genérico no SQLite.
    """
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())


class Base(DeclarativeBase):
    """Classe base declarativa para todas as entidades ORM."""
    pass


# Criação da Engine de Conexão
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator:
    """
    Injetor de dependência para sessões de banco de dados do FastAPI.
    Garante fechamento e liberação da conexão ao término da requisição.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

