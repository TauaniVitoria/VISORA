"""
Testes unitários e de integração para autenticação JWT e controle de acesso RBAC.
"""

from fastapi.testclient import TestClient

from app.models.entities import Usuario


def test_login_success(client: TestClient, tenant_a_admin: Usuario):
    """Valida login com credenciais válidas retornando token e claims corretos."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "gerente@central.com", "senha": "senha123456"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["perfil"] == "ESTACIONAMENTO_ADMIN"
    assert data["email"] == "gerente@central.com"


def test_login_invalid_password(client: TestClient, tenant_a_admin: Usuario):
    """Valida rejeição de login com senha incorreta."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "gerente@central.com", "senha": "senha_errada"},
    )
    assert response.status_code == 401
    assert "incorretos" in response.json()["detail"]


def test_get_current_user_profile(client: TestClient, tenant_a_token: str):
    """Valida rota protegida /auth/me com token válido."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tenant_a_token}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "gerente@central.com"


def test_rbac_saas_admin_only_routes(client: TestClient, tenant_a_token: str, saas_admin_token: str):
    """
    Garante que rotas exclusivas do SaaS Admin (como criar e listar estacionamentos)
    rejeitem administradores locais com status 403 Forbidden.
    """
    # Tentativa de listar tenants como ESTACIONAMENTO_ADMIN -> Deve falhar com 403
    resp_forbidden = client.get(
        "/api/v1/tenants/",
        headers={"Authorization": f"Bearer {tenant_a_token}"},
    )
    assert resp_forbidden.status_code == 403

    # Tentativa com token de SAAS_ADMIN -> Sucesso 200
    resp_allowed = client.get(
        "/api/v1/tenants/",
        headers={"Authorization": f"Bearer {saas_admin_token}"},
    )
    assert resp_allowed.status_code == 200

