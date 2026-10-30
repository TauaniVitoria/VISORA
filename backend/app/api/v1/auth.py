"""
Endpoints de autenticação e sessão.
"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.core.security import create_access_token
from app.models.entities import Usuario, UsuarioPerfil
from app.schemas.schemas import (
    LoginRequest,
    MessageOut,
    PasswordRecoveryRequest,
    PasswordResetConfirm,
    Token,
    UsuarioCreate,
    UsuarioOut,
)
from app.services.business_services import AuthService

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/login", response_model=Token)
def login(login_in: LoginRequest, db: Session = Depends(get_db)) -> Any:
    """Autentica usuário e retorna token JWT com claims de perfil e tenant."""
    user = AuthService.authenticate_user(db, login_in.email, login_in.senha)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    claims = {
        "perfil": user.perfil,
        "estacionamento_id": str(user.estacionamento_id) if user.estacionamento_id else None,
        "nome": user.nome,
    }
    access_token = create_access_token(subject=str(user.id), claims=claims)

    return Token(
        access_token=access_token,
        token_type="bearer",
        perfil=user.perfil,
        nome=user.nome,
        email=user.email,
        estacionamento_id=user.estacionamento_id,
    )


@router.post("/register", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def register(
    user_in: UsuarioCreate,
    current_user: Usuario = Depends(
        require_roles(UsuarioPerfil.ESTACIONAMENTO_ADMIN, UsuarioPerfil.SAAS_ADMIN)
    ),
    db: Session = Depends(get_db),
) -> Any:
    """
    Cadastro de usuário administrativo (exige autenticação).
    SAAS_ADMIN cria administradores de qualquer estacionamento; ESTACIONAMENTO_ADMIN
    cria administradores apenas no próprio estacionamento.
    """
    return AuthService.register_user(db, current_user, user_in)


@router.post("/forgot-password", response_model=MessageOut)
def forgot_password(req: PasswordRecoveryRequest, db: Session = Depends(get_db)) -> Any:
    """Solicita o link de redefinição. A resposta é sempre a mesma, exista ou não o e-mail."""
    AuthService.request_password_reset(db, req.email)
    return MessageOut(detail="Se o e-mail estiver cadastrado, enviaremos as instruções de recuperação.")


@router.post("/reset-password", response_model=MessageOut)
def reset_password(req: PasswordResetConfirm, db: Session = Depends(get_db)) -> Any:
    """Redefine a senha com o token recebido por e-mail (uso único, curta duração)."""
    AuthService.reset_password(db, req.token, req.nova_senha)
    return MessageOut(detail="Senha redefinida com sucesso.")


@router.get("/me", response_model=UsuarioOut)
def get_me(current_user: Usuario = Depends(get_current_user)) -> Any:
    """Retorna os dados do usuário autenticado atual."""
    return current_user

