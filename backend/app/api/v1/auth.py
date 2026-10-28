"""
Endpoints de autenticação e sessão.
"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.security import create_access_token
from app.models.entities import Usuario
from app.schemas.schemas import LoginRequest, Token, UsuarioCreate, UsuarioOut
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
def register(user_in: UsuarioCreate, db: Session = Depends(get_db)) -> Any:
    """Cadastro de novo usuário administrativo."""
    return AuthService.create_user(db, user_in)


@router.get("/me", response_model=UsuarioOut)
def get_me(current_user: Usuario = Depends(get_current_user)) -> Any:
    """Retorna os dados do usuário autenticado atual."""
    return current_user

