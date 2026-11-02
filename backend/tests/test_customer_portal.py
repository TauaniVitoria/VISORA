"""
Testes da Fase 6: Portal do Cliente, política de cadastro de usuários e recuperação de senha.
Foco em isolamento (entre clientes e entre estacionamentos) e em RBAC do perfil CLIENTE.
"""

from datetime import datetime, timedelta, timezone
import logging
from typing import Dict, List
import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.models.entities import Estacionamento, Usuario

CLIENT_PASSWORD = "cliente-senha-123"


def bearer(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def make_customer(client: TestClient, headers: Dict[str, str], nome: str, documento: str, placa: str) -> Dict:
    resp = client.post(
        "/api/v1/customers/",
        headers=headers,
        json={
            "nome": nome,
            "documento": documento,
            "tipo_documento": "CPF",
            "telefone": "(11) 98888-0000",
            "plano_tipo": "diario",
            "email": f"contato.{placa.lower()}@mail.com",
            "veiculos_iniciais": [{"placa": placa, "marca": "Fiat", "modelo": "Uno", "cor": "Prata", "tipo": "carro"}],
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def grant_portal_access(client: TestClient, headers: Dict[str, str], customer: Dict, email: str) -> Dict[str, str]:
    resp = client.post(
        f"/api/v1/customers/{customer['id']}/portal-access",
        headers=headers,
        json={"email": email, "senha": CLIENT_PASSWORD},
    )
    assert resp.status_code == 201, resp.text
    login = client.post("/api/v1/auth/login", json={"email": email, "senha": CLIENT_PASSWORD})
    assert login.status_code == 200, login.text
    return bearer(login.json()["access_token"])


def stay(client: TestClient, headers: Dict[str, str], placa: str, minutes: int, close: bool = True) -> Dict:
    """Cria uma permanência de `minutes` minutos; fecha com saída se `close`."""
    entry = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    r_in = client.post(
        "/api/v1/movements/entry", json={"placa": placa, "timestamp": entry.isoformat()}, headers=headers
    )
    assert r_in.status_code in (200, 201), r_in.text
    if not close:
        return r_in.json()
    r_out = client.post(
        "/api/v1/movements/exit",
        json={"placa": placa, "timestamp": datetime.now(timezone.utc).isoformat()},
        headers=headers,
    )
    assert r_out.status_code == 200, r_out.text
    return r_out.json()


# ---------------------------------------------------------------- cadastro de usuários

def test_register_requires_authentication(client: TestClient, tenant_a: Estacionamento):
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "nome": "Intruso",
            "email": "intruso@x.com",
            "senha": "12345678",
            "perfil": "SAAS_ADMIN",
        },
    )
    assert resp.status_code in (401, 403)


def test_register_blocks_privilege_escalation(
    client: TestClient,
    tenant_a_token: str,
    tenant_a: Estacionamento,
    tenant_b: Estacionamento,
    saas_admin_token: str,
):
    h = bearer(tenant_a_token)
    base = {"nome": "Novo", "senha": "12345678"}

    # Admin de estacionamento não cria SAAS_ADMIN
    r = client.post("/api/v1/auth/register", headers=h, json={**base, "email": "a1@x.com", "perfil": "SAAS_ADMIN"})
    assert r.status_code == 403

    # Nem usuários em outro estacionamento
    r = client.post(
        "/api/v1/auth/register",
        headers=h,
        json={**base, "email": "a2@x.com", "perfil": "ESTACIONAMENTO_ADMIN", "estacionamento_id": str(tenant_b.id)},
    )
    assert r.status_code == 403

    # Sem estacionamento informado, é forçado o próprio
    r = client.post(
        "/api/v1/auth/register", headers=h, json={**base, "email": "a3@x.com", "perfil": "ESTACIONAMENTO_ADMIN"}
    )
    assert r.status_code == 201
    assert r.json()["estacionamento_id"] == str(tenant_a.id)

    # CLIENTE não nasce por /register
    r = client.post(
        "/api/v1/auth/register",
        headers=h,
        json={**base, "email": "a4@x.com", "perfil": "CLIENTE", "estacionamento_id": str(tenant_a.id)},
    )
    assert r.status_code == 400

    # SAAS_ADMIN pode criar outro SAAS_ADMIN
    r = client.post(
        "/api/v1/auth/register",
        headers=bearer(saas_admin_token),
        json={**base, "email": "root2@x.com", "perfil": "SAAS_ADMIN"},
    )
    assert r.status_code == 201


# ---------------------------------------------------------------- acesso ao portal

def test_portal_access_lifecycle(client: TestClient, tenant_a_token: str):
    admin = bearer(tenant_a_token)
    customer = make_customer(client, admin, "Maria Souza", "12345678901", "ABC1D23")
    assert customer["acesso_portal"] is False
    portal = grant_portal_access(client, admin, customer, "maria@mail.com")

    listed = {c["id"]: c for c in client.get("/api/v1/customers/", headers=admin).json()}
    assert listed[customer["id"]]["acesso_portal"] is True

    me = client.get("/api/v1/portal/me", headers=portal)
    assert me.status_code == 200
    data = me.json()
    assert data["nome"] == "Maria Souza"
    assert data["documento_mascarado"] == "*******8901"
    assert "12345678901" not in me.text
    assert [v["placa"] for v in data["veiculos"]] == ["ABC1D23"]

    # segundo acesso para o mesmo cliente é recusado
    dup = client.post(
        f"/api/v1/customers/{customer['id']}/portal-access",
        headers=admin,
        json={"email": "outro@mail.com", "senha": CLIENT_PASSWORD},
    )
    assert dup.status_code == 400

    # revogação impede novo login e invalida o token em uso
    assert client.delete(f"/api/v1/customers/{customer['id']}/portal-access", headers=admin).status_code == 204
    assert client.post(
        "/api/v1/auth/login", json={"email": "maria@mail.com", "senha": CLIENT_PASSWORD}
    ).status_code == 401
    assert client.get("/api/v1/portal/me", headers=portal).status_code == 401
    listed = {c["id"]: c for c in client.get("/api/v1/customers/", headers=admin).json()}
    assert listed[customer["id"]]["acesso_portal"] is False


def test_portal_access_cannot_target_other_tenant_customer(
    client: TestClient, tenant_a_token: str, tenant_b_token: str
):
    customer_b = make_customer(client, bearer(tenant_b_token), "Cliente B", "11122233344", "BBB1B11")
    resp = client.post(
        f"/api/v1/customers/{customer_b['id']}/portal-access",
        headers=bearer(tenant_a_token),
        json={"email": "invasor@mail.com", "senha": CLIENT_PASSWORD},
    )
    assert resp.status_code == 404


ADMIN_ONLY_ROUTES = [
    ("get", "/api/v1/customers/"),
    ("get", "/api/v1/movements/history"),
    ("get", "/api/v1/movements/active"),
    ("post", "/api/v1/movements/entry"),
    ("get", "/api/v1/billing/charges"),
    ("post", "/api/v1/billing/payments"),
    ("get", "/api/v1/dashboard/metrics"),
    ("get", "/api/v1/audit/"),
    ("get", "/api/v1/tenants/"),
    ("get", "/api/v1/cameras/"),
    ("post", "/api/v1/cameras/"),
    ("post", "/api/v1/alpr/simulate-detection"),
    ("post", "/api/v1/alpr/process-video"),
    ("post", "/api/v1/auth/register"),
]


@pytest.mark.parametrize("method,url", ADMIN_ONLY_ROUTES)
def test_cliente_is_forbidden_on_admin_routes(client: TestClient, tenant_a_token: str, method: str, url: str):
    admin = bearer(tenant_a_token)
    customer = make_customer(client, admin, "Cliente RBAC", "55566677788", "RBA1A11")
    portal = grant_portal_access(client, admin, customer, "rbac@mail.com")
    resp = getattr(client, method)(url, headers=portal, json={}) if method == "post" else client.get(url, headers=portal)
    assert resp.status_code == 403, f"{method.upper()} {url} -> {resp.status_code}"


def test_admin_cannot_use_portal_routes(client: TestClient, tenant_a_token: str):
    assert client.get("/api/v1/portal/me", headers=bearer(tenant_a_token)).status_code == 403


def test_portal_requires_authentication(client: TestClient):
    assert client.get("/api/v1/portal/me").status_code in (401, 403)


# ---------------------------------------------------------------- isolamento de dados

def test_portal_data_isolated_between_clients_and_tenants(
    client: TestClient, tenant_a_token: str, tenant_b_token: str
):
    a, b = bearer(tenant_a_token), bearer(tenant_b_token)

    c1 = make_customer(client, a, "Cliente Um", "10000000001", "AAA1A11")
    c2 = make_customer(client, a, "Cliente Dois", "10000000002", "BBB2B22")
    # Mesma placa em OUTRO estacionamento (permitido: unicidade é por tenant)
    make_customer(client, b, "Cliente Outro Tenant", "10000000003", "AAA1A11")

    stay(client, a, "AAA1A11", 30)
    stay(client, a, "BBB2B22", 30)
    stay(client, b, "AAA1A11", 30)
    stay(client, b, "AAA1A11", 40)

    portal1 = grant_portal_access(client, a, c1, "um@mail.com")
    portal2 = grant_portal_access(client, a, c2, "dois@mail.com")

    movs1 = client.get("/api/v1/portal/movements", headers=portal1).json()
    assert [m["placa"] for m in movs1] == ["AAA1A11"]  # nem a placa do cliente 2, nem as passagens do tenant B

    movs2 = client.get("/api/v1/portal/movements", headers=portal2).json()
    assert [m["placa"] for m in movs2] == ["BBB2B22"]

    charges1 = client.get("/api/v1/portal/charges", headers=portal1).json()
    assert len(charges1) == 1
    pay1 = client.get("/api/v1/portal/payments", headers=portal1).json()
    assert pay1 == []

    vehicles2 = client.get("/api/v1/portal/vehicles", headers=portal2).json()
    assert [v["placa"] for v in vehicles2] == ["BBB2B22"]


def test_portal_ignores_client_supplied_scope(client: TestClient, tenant_a_token: str):
    """Parâmetros como cliente_id/estacionamento_id na query não alteram o escopo."""
    a = bearer(tenant_a_token)
    c1 = make_customer(client, a, "Cliente Um", "20000000001", "CCC1C11")
    c2 = make_customer(client, a, "Cliente Dois", "20000000002", "DDD2D22")
    stay(client, a, "DDD2D22", 30)
    portal1 = grant_portal_access(client, a, c1, "c1@mail.com")
    resp = client.get(
        f"/api/v1/portal/movements?cliente_id={c2['id']}&estacionamento_id={uuid.uuid4()}", headers=portal1
    )
    assert resp.status_code == 200
    assert resp.json() == []


# ---------------------------------------------------------------- conteúdo do portal

def test_portal_open_stay_shows_running_permanence_and_hides_internal_fields(
    client: TestClient, tenant_a_token: str
):
    a = bearer(tenant_a_token)
    customer = make_customer(client, a, "Cliente Aberto", "30000000001", "EEE1E11")
    stay(client, a, "EEE1E11", 45, close=False)
    portal = grant_portal_access(client, a, customer, "aberto@mail.com")

    movs = client.get("/api/v1/portal/movements", headers=portal).json()
    assert len(movs) == 1
    assert movs[0]["em_andamento"] is True
    assert movs[0]["status"] == "aberta"
    assert 44 <= movs[0]["permanencia_minutos"] <= 47
    for internal in ("observacao", "camera_entrada_id", "camera_saida_id", "estacionamento_id"):
        assert internal not in movs[0]

    summary = client.get("/api/v1/portal/summary", headers=portal).json()
    assert summary["veiculos_cadastrados"] == 1
    assert [m["placa"] for m in summary["veiculos_estacionados"]] == ["EEE1E11"]


def test_portal_charges_and_payments_flow(client: TestClient, tenant_a_token: str):
    a = bearer(tenant_a_token)
    customer = make_customer(client, a, "Cliente Cobrança", "40000000001", "FFF1F11")
    closed = stay(client, a, "FFF1F11", 30)
    portal = grant_portal_access(client, a, customer, "cobranca@mail.com")

    pending = client.get("/api/v1/portal/charges?status_filter=pendente", headers=portal).json()
    assert len(pending) == 1
    summary = client.get("/api/v1/portal/summary", headers=portal).json()
    assert summary["cobrancas_pendentes_quantidade"] == 1
    assert float(summary["cobrancas_pendentes_valor"]) == float(pending[0]["valor_liquido"]) > 0

    # O cliente não consegue pagar/alterar nada pelo portal
    assert client.post("/api/v1/billing/payments", headers=portal, json={}).status_code == 403

    # Administrador registra o pagamento; o cliente passa a ver cobrança paga e o pagamento
    pay = client.post(
        "/api/v1/billing/payments",
        headers=a,
        json={
            "cobranca_id": closed["cobranca"]["id"],
            "valor_pago": pending[0]["valor_liquido"],
            "metodo": "pix",
        },
    )
    assert pay.status_code == 201

    assert client.get("/api/v1/portal/charges?status_filter=pendente", headers=portal).json() == []
    payments = client.get("/api/v1/portal/payments", headers=portal).json()
    assert len(payments) == 1
    assert payments[0]["metodo"] == "pix"
    assert "registrado_por_usuario_id" not in payments[0]


def test_portal_subscriptions_and_plans(client: TestClient, tenant_a_token: str, tenant_b_token: str):
    a, b = bearer(tenant_a_token), bearer(tenant_b_token)
    customer = make_customer(client, a, "Cliente Plano", "50000000001", "GGG1G11")
    vehicle_id = customer["veiculos"][0]["id"]

    plan_payload = {"tipo_recorrencia": "diario", "valor_base": "50.00", "limite_veiculos": 1}
    plan = client.post("/api/v1/tariffs-plans/plans", headers=a, json={"nome": "Diario Livre", **plan_payload})
    assert plan.status_code == 201, plan.text
    client.post("/api/v1/tariffs-plans/plans", headers=b, json={"nome": "Plano do Tenant B", **plan_payload})

    sub = client.post(
        "/api/v1/tariffs-plans/subscriptions",
        headers=a,
        json={
            "cliente_id": customer["id"],
            "plano_id": plan.json()["id"],
            "veiculos_ids": [vehicle_id],
            "data_inicio": datetime.now(timezone.utc).date().isoformat(),
        },
    )
    assert sub.status_code == 201, sub.text

    portal = grant_portal_access(client, a, customer, "plano@mail.com")

    subs = client.get("/api/v1/portal/subscriptions", headers=portal).json()
    assert len(subs) == 1
    assert subs[0]["plano_nome"] == "Diario Livre"
    assert subs[0]["placas"] == ["GGG1G11"]
    assert subs[0]["status"] == "ativa"

    plans = client.get("/api/v1/portal/plans", headers=portal).json()
    assert [p["nome"] for p in plans] == ["Diario Livre"]  # plano do tenant B não aparece

    summary = client.get("/api/v1/portal/summary", headers=portal).json()
    assert summary["assinaturas_ativas"] == 1


# ---------------------------------------------------------------- recuperação de senha

@pytest.fixture
def sent_tokens(monkeypatch: pytest.MonkeyPatch) -> List[Dict[str, str]]:
    sent: List[Dict[str, str]] = []
    monkeypatch.setattr(
        "app.services.business_services.send_password_reset_email",
        lambda email, token: sent.append({"email": email, "token": token}),
    )
    return sent


def test_forgot_password_does_not_reveal_accounts(
    client: TestClient, tenant_a_admin: Usuario, sent_tokens: List[Dict[str, str]]
):
    known = client.post("/api/v1/auth/forgot-password", json={"email": "gerente@central.com"})
    unknown = client.post("/api/v1/auth/forgot-password", json={"email": "ninguem@nada.com"})
    assert known.status_code == unknown.status_code == 200
    assert known.json() == unknown.json()
    assert [s["email"] for s in sent_tokens] == ["gerente@central.com"]


def test_password_reset_flow_is_single_use(
    client: TestClient, tenant_a_admin: Usuario, sent_tokens: List[Dict[str, str]]
):
    client.post("/api/v1/auth/forgot-password", json={"email": "gerente@central.com"})
    token = sent_tokens[0]["token"]

    # token de reset não funciona como token de acesso
    assert client.get("/api/v1/auth/me", headers=bearer(token)).status_code == 401

    ok = client.post("/api/v1/auth/reset-password", json={"token": token, "nova_senha": "nova-senha-456"})
    assert ok.status_code == 200

    assert client.post(
        "/api/v1/auth/login", json={"email": "gerente@central.com", "senha": "senha123456"}
    ).status_code == 401
    assert client.post(
        "/api/v1/auth/login", json={"email": "gerente@central.com", "senha": "nova-senha-456"}
    ).status_code == 200

    # reutilizar o mesmo token falha
    again = client.post("/api/v1/auth/reset-password", json={"token": token, "nova_senha": "outra-senha-789"})
    assert again.status_code == 400


def test_password_reset_rejects_bad_tokens(client: TestClient, tenant_a_admin: Usuario, tenant_a_token: str):
    # token de acesso comum não serve para reset
    r = client.post("/api/v1/auth/reset-password", json={"token": tenant_a_token, "nova_senha": "nova-senha-456"})
    assert r.status_code == 400

    # token expirado
    expired = create_access_token(
        subject=str(tenant_a_admin.id),
        claims={"purpose": "password_reset", "pwd": "x"},
        expires_delta=timedelta(minutes=-1),
    )
    r = client.post("/api/v1/auth/reset-password", json={"token": expired, "nova_senha": "nova-senha-456"})
    assert r.status_code == 400

    # lixo
    r = client.post("/api/v1/auth/reset-password", json={"token": "x" * 40, "nova_senha": "nova-senha-456"})
    assert r.status_code == 400

    # senha curta é rejeitada pela validação
    r = client.post("/api/v1/auth/reset-password", json={"token": "x" * 40, "nova_senha": "curta"})
    assert r.status_code == 422


# ---------------------------------------------------------------- notificações

def test_email_sent_via_smtp_when_configured(monkeypatch: pytest.MonkeyPatch):
    from app.core.config import settings
    from app.services import notification_service

    calls: Dict = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout=None):
            calls["host"], calls["port"] = host, port

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def starttls(self):
            calls["tls"] = True

        def login(self, user, password):
            calls["login"] = user

        def send_message(self, msg):
            calls["to"] = msg["To"]
            calls["body"] = msg.get_content()

    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.exemplo.com")
    monkeypatch.setattr(settings, "SMTP_USER", "u")
    monkeypatch.setattr(notification_service.smtplib, "SMTP", FakeSMTP)

    notification_service.send_password_reset_email("alguem@mail.com", "TOKEN123")
    assert calls["tls"] is True
    assert calls["to"] == "alguem@mail.com"
    assert "reset-password?token=TOKEN123" in calls["body"]


def test_token_never_logged_in_production_without_smtp(monkeypatch: pytest.MonkeyPatch, caplog):
    from app.core.config import settings
    from app.services import notification_service

    monkeypatch.setattr(settings, "SMTP_HOST", "")
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    with caplog.at_level(logging.INFO, logger="alpr.notifications"):
        notification_service.send_password_reset_email("alguem@mail.com", "SEGREDO-TOKEN")
    assert "SEGREDO-TOKEN" not in caplog.text
