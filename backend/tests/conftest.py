"""
Configurações e fixtures globais de teste para o Backend FastAPI.
Utiliza banco de dados SQLite isolado em memória e TestClient.
"""

import os
# Configuração de variáveis de ambiente para modo de teste ANTES de qualquer importação
os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.database import Base
from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.models.entities import Estacionamento, EstacionamentoStatus, Usuario, UsuarioPerfil

# Engine em memória persistente durante a sessão de teste
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Cria todas as tabelas no banco de dados em memória no início dos testes."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Fornece uma sessão de banco limpa e isolada para cada teste."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """TestClient configurado com override da dependência de banco de dados."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def saas_admin_user(db_session: Session) -> Usuario:
    """Cria e retorna um usuário SaaS Admin."""
    user = Usuario(
        nome="Super Admin",
        email="saas_admin@platform.com",
        senha_hash=get_password_hash("admin123456"),
        perfil=UsuarioPerfil.SAAS_ADMIN.value,
        estacionamento_id=None,
        ativo=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def saas_admin_token(saas_admin_user: Usuario) -> str:
    """Token de acesso para o SaaS Admin."""
    claims = {"perfil": saas_admin_user.perfil, "estacionamento_id": None}
    return create_access_token(subject=str(saas_admin_user.id), claims=claims)


@pytest.fixture
def tenant_a(db_session: Session) -> Estacionamento:
    """Cria o Estacionamento A."""
    est = Estacionamento(
        nome_fantasia="Estacionamento Central",
        razao_social="Central Parkings Ltda",
        cnpj="11222333000144",
        email_contato="contato@central.com",
        status=EstacionamentoStatus.ATIVO.value,
    )
    db_session.add(est)
    db_session.commit()
    db_session.refresh(est)
    return est


@pytest.fixture
def tenant_a_admin(db_session: Session, tenant_a: Estacionamento) -> Usuario:
    """Cria o Administrador do Estacionamento A."""
    user = Usuario(
        nome="Gerente Central",
        email="gerente@central.com",
        senha_hash=get_password_hash("senha123456"),
        perfil=UsuarioPerfil.ESTACIONAMENTO_ADMIN.value,
        estacionamento_id=tenant_a.id,
        ativo=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def tenant_a_token(tenant_a_admin: Usuario, tenant_a: Estacionamento) -> str:
    """Token de acesso para o Administrador do Estacionamento A."""
    claims = {"perfil": tenant_a_admin.perfil, "estacionamento_id": str(tenant_a.id)}
    return create_access_token(subject=str(tenant_a_admin.id), claims=claims)


@pytest.fixture
def tenant_b(db_session: Session) -> Estacionamento:
    """Cria o Estacionamento B."""
    est = Estacionamento(
        nome_fantasia="Estacionamento Norte",
        razao_social="Norte Estacionamentos Ltda",
        cnpj="99888777000155",
        email_contato="contato@norte.com",
        status=EstacionamentoStatus.ATIVO.value,
    )
    db_session.add(est)
    db_session.commit()
    db_session.refresh(est)
    return est


@pytest.fixture
def tenant_b_admin(db_session: Session, tenant_b: Estacionamento) -> Usuario:
    """Cria o Administrador do Estacionamento B."""
    user = Usuario(
        nome="Gerente Norte",
        email="gerente@norte.com",
        senha_hash=get_password_hash("senha123456"),
        perfil=UsuarioPerfil.ESTACIONAMENTO_ADMIN.value,
        estacionamento_id=tenant_b.id,
        ativo=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def tenant_b_token(tenant_b_admin: Usuario, tenant_b: Estacionamento) -> str:
    """Token de acesso para o Administrador do Estacionamento B."""
    claims = {"perfil": tenant_b_admin.perfil, "estacionamento_id": str(tenant_b.id)}
    return create_access_token(subject=str(tenant_b_admin.id), claims=claims)
