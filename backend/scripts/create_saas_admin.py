"""
Cria o primeiro administrador SaaS (bootstrap).

Como /auth/register exige autenticação, este script é o caminho para criar o primeiro usuário.
A senha é lida de SAAS_ADMIN_PASSWORD (ou solicitada no terminal), nunca de argumento de linha de comando.

Uso (a partir da pasta backend/):
    SAAS_ADMIN_PASSWORD='...' python scripts/create_saas_admin.py --email admin@empresa.com --nome "Admin"
"""

import argparse
import getpass
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import SessionLocal  # noqa: E402
from app.models.entities import UsuarioPerfil  # noqa: E402
from app.schemas.schemas import UsuarioCreate  # noqa: E402
from app.services.business_services import AuthService  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Cria o primeiro SAAS_ADMIN.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--nome", default="Administrador SaaS")
    args = parser.parse_args()

    senha = os.environ.get("SAAS_ADMIN_PASSWORD") or getpass.getpass("Senha (mín. 8 caracteres): ")
    if len(senha) < 8:
        sys.exit("A senha deve ter pelo menos 8 caracteres.")

    with SessionLocal() as db:
        user = AuthService.create_user(
            db,
            UsuarioCreate(nome=args.nome, email=args.email, senha=senha, perfil=UsuarioPerfil.SAAS_ADMIN),
        )
        print(f"SAAS_ADMIN criado: {user.email} ({user.id})")


if __name__ == "__main__":
    main()
