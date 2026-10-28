"""
Injetores de dependência para autenticação, autorização por perfil (RBAC)
e isolamento estrito multi-tenant.
"""

from typing import List, Optional
import uuid
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.entities import Usuario, UsuarioPerfil

security_bearer = HTTPBearer(auto_error=True)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    """Extrai e valida o token JWT, retornando o usuário autenticado."""
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id_str: Optional[str] = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de autenticação inválido (subject ausente).",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_uuid = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais de autenticação inválidas ou expiradas.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    stmt = select(Usuario).where(Usuario.id == user_uuid)
    user = db.scalar(stmt)
    if not user or not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário inativo ou inexistente.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_roles(*allowed_roles: UsuarioPerfil):
    """Fábrica de dependência para controle de acesso baseado em papéis (RBAC)."""
    def role_checker(current_user: Usuario = Depends(get_current_user)) -> Usuario:
        allowed_str_values = [r.value for r in allowed_roles]
        if current_user.perfil not in allowed_str_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso não autorizado para o perfil do usuário.",
            )
        return current_user
    return role_checker


def get_current_tenant_id(
    current_user: Usuario = Depends(get_current_user),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
) -> uuid.UUID:
    """
    Garante o isolamento multi-tenant.
    Para administradores de estacionamento e clientes, o tenant é estritamente o do seu cadastro.
    Para o SAAS_ADMIN, permite navegar especificando o header X-Tenant-ID.
    """
    if current_user.perfil == UsuarioPerfil.SAAS_ADMIN.value:
        if x_tenant_id:
            try:
                return uuid.UUID(x_tenant_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Formato inválido de X-Tenant-ID.",
                )
        if current_user.estacionamento_id:
            return current_user.estacionamento_id
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Header X-Tenant-ID é obrigatório para operações de escopo de estacionamento como SAAS_ADMIN.",
        )

    if not current_user.estacionamento_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário não vinculado a nenhum estacionamento.",
        )

    return current_user.estacionamento_id

